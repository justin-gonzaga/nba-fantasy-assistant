import values from '../fixtures/values-2026-27.json'
import type { DraftPlayer } from '../live'
import { ME, fastForward, nominate, pass, start, type Practice, type Settings } from '../practice'
import type { AudioPort, AudioStatus } from './audio'
import { CUE_GAP_MS, createCuePlayer, cuesFor, tickCue } from './cues'
import { DEFAULT_FX, type FxPrefs } from './prefs'
import type { Cue } from './voices'

const players = values.players as DraftPlayer[]
const settings: Settings = { seed: 5, styles: 'mix', punted: null, pace: 'untimed' }

function toMyNomination(p: Practice): Practice {
  let cur = p
  while (cur.phase === 'lot') cur = pass(cur)
  return cur
}
/** A state with an open lot the owner nominated, and the state just before it. */
function openLot(): { before: Practice; lot: Practice } {
  const before = toMyNomination(start(players, settings))
  const taken = new Set(before.room.sales.map((s) => s.pid))
  const pid = (players.find((x) => !taken.has(x.id)) as DraftPlayer).id
  return { before, lot: nominate(before, pid) }
}

describe('cuesFor: what changed gives which cues (DRAFT-020 AC3)', () => {
  it('the owner opening a lot plays nominate', () => {
    const { before, lot } = openLot()
    expect(cuesFor(before, lot)).toEqual(['nominate'])
  })

  it('a price rise in the same lot plays bid, plus outbid when a rival is high', () => {
    const { lot } = openLot()
    const l = lot.lot as NonNullable<typeof lot.lot>
    const rival = { ...lot, lot: { ...l, price: l.price + 1, high: 'Team 2' } }
    const mine = { ...lot, lot: { ...l, price: l.price + 1, high: ME } }
    expect(cuesFor(lot, rival)).toEqual(['bid', 'outbid'])
    expect(cuesFor(lot, mine)).toEqual(['bid'])
  })

  it('a sale plays soldYou or soldOther by the buyer', () => {
    const { lot } = openLot()
    const after = pass(lot)
    const buyer = after.room.sales[lot.room.sales.length]?.team
    expect(cuesFor(lot, after)[0]).toBe(buyer === ME ? 'soldYou' : 'soldOther')
  })

  it('plays nothing when nothing changed', () => {
    const { lot } = openLot()
    expect(cuesFor(lot, lot)).toEqual([])
  })

  it('undo (fewer sales) plays nothing', () => {
    const { lot } = openLot()
    expect(cuesFor(pass(lot), lot)).toEqual([])
  })

  it('fast-forward is silent except for the end of the draft', () => {
    const { lot } = openLot()
    const some = fastForward(lot, true)
    expect(some.room.sales.length).toBeGreaterThan(lot.room.sales.length)
    if (some.phase !== 'done') expect(cuesFor(lot, some, { fastForward: true })).toEqual([])
    const end = fastForward(lot, false)
    expect(end.phase).toBe('done')
    expect(cuesFor(lot, end, { fastForward: true })).toEqual(['done'])
    expect(cuesFor(lot, end)).toEqual(['done'])
  })
})

describe('tickCue: half-second index gives a cue', () => {
  // h = ceil(ms left / 500): a whole second s is h = 2s, the half second before it is 2s - 1
  const whole = (s: number) => s * 2
  const half = (s: number) => s * 2 - 1
  it('off never ticks', () => {
    for (const x of [20, 10, 2, 1]) expect(tickCue(x, 'off')).toBeNull()
  })
  it('last10 ticks once a second from 10 s, none before', () => {
    expect(tickCue(whole(10), 'last10')).toBe('tick')
    expect(tickCue(half(10), 'last10')).toBeNull()
    expect(tickCue(whole(6), 'last10')).toBe('tick')
    expect(tickCue(whole(11), 'last10')).toBeNull()
  })
  it('every ticks each whole second', () => {
    expect(tickCue(whole(11), 'every')).toBe('tick')
    expect(tickCue(whole(30), 'every')).toBe('tick')
    expect(tickCue(half(11), 'every')).toBeNull()
  })
  it('the last 5 s tick on every half second, higher', () => {
    expect(tickCue(whole(5), 'last10')).toBe('tickUrgent')
    expect(tickCue(half(5), 'last10')).toBe('tickUrgent')
    expect(tickCue(whole(1), 'every')).toBe('tickUrgent')
    expect(tickCue(0, 'every')).toBeNull()
  })
})

describe('createCuePlayer: mute, hidden tab and no flood (DRAFT-020 AC3)', () => {
  let clock = 0
  let prefs: FxPrefs
  let hidden = false
  let status: AudioStatus
  let played: Cue[]
  const port: AudioPort = {
    play: (c) => void played.push(c),
    setVolume: () => {},
    unlock: () => Promise.resolve('running'),
    status: () => status,
    subscribe: () => () => {},
  }
  const make = () =>
    createCuePlayer({
      port: () => port,
      prefs: () => prefs,
      hidden: () => hidden,
      now: () => clock,
    })

  beforeEach(() => {
    vi.useFakeTimers()
    clock = 0
    prefs = DEFAULT_FX
    hidden = false
    status = 'running'
    played = []
  })
  afterEach(() => vi.useRealTimers())

  it('plays the first cue at once and spaces the next ones', () => {
    const p = make()
    p.play('bid')
    p.play('outbid')
    expect(played).toEqual(['bid'])
    vi.advanceTimersByTime(CUE_GAP_MS)
    expect(played).toEqual(['bid', 'outbid'])
  })

  it('drops cues beyond the short backlog (no flood)', () => {
    const p = make()
    for (let i = 0; i < 10; i++) p.play('tick')
    vi.advanceTimersByTime(5000)
    expect(played.length).toBe(4)
  })

  it('plays nothing when muted, hidden or the context is not running', () => {
    prefs = { ...DEFAULT_FX, muted: true }
    make().play('bid')
    prefs = DEFAULT_FX
    hidden = true
    make().play('bid')
    hidden = false
    status = 'suspended'
    make().play('bid')
    expect(played).toEqual([])
  })

  it('dispose drops cues still waiting', () => {
    const p = make()
    p.play('bid')
    p.play('outbid')
    p.dispose()
    vi.advanceTimersByTime(1000)
    expect(played).toEqual(['bid'])
  })

  it('a queued cue is dropped if the owner mutes before it fires', () => {
    const p = make()
    p.play('bid')
    p.play('outbid')
    prefs = { ...DEFAULT_FX, muted: true }
    vi.advanceTimersByTime(1000)
    expect(played).toEqual(['bid'])
  })
})
