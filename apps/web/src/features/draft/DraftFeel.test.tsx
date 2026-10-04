import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players } from '../../api/types'
import { CATEGORIES } from '../players/format'
import type { AudioPort, AudioStatus } from './fx/audio'
import { setAudioPort } from './fx/audio'
import { FX_KEY } from './fx/prefs'
import type { Cue } from './fx/voices'
import values from './fixtures/values-2026-27.json'

const base = samplePlayers.players[0] as PlayerRow
const rows: PlayerRow[] = values.players.map((v, i) => ({
  ...base,
  id: Number(v.id),
  name: `Player ${v.id}`,
  rank: i + 1,
  dollars: v.usd,
  badges: [],
  indicators: [],
  strengths: Object.fromEntries(CATEGORIES.map(([k], j) => [k, v.z[j] ?? 0])),
}))
const full: Players = { ...samplePlayers, players: rows }
const client: ApiClient = { ...fixtureClient, players: () => Promise.resolve(full) }

let played: Cue[]
let status: AudioStatus
let unlocked: number
const listeners = new Set<() => void>()
const setStatus = (s: AudioStatus) => {
  status = s
  listeners.forEach((fn) => fn())
}
const defaultUnlock = () => {
  unlocked += 1
  setStatus('running')
  return Promise.resolve<AudioStatus>('running')
}
const port: AudioPort = {
  play: (c) => void played.push(c),
  setVolume: () => {},
  unlock: defaultUnlock,
  status: () => status,
  subscribe: (fn) => {
    listeners.add(fn)
    return () => void listeners.delete(fn)
  },
}

async function startDraft(pace: 'Real timers' | 'Untimed') {
  render(<App client={client} initialPath="/draft" />)
  fireEvent.click(await screen.findByRole('radio', { name: new RegExp(pace) }))
  fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
}

beforeEach(() => {
  vi.spyOn(Math, 'random').mockReturnValue(0.123)
  localStorage.clear()
  played = []
  unlocked = 0
  status = 'running'
  listeners.clear()
  port.unlock = defaultUnlock
  setAudioPort(port)
})
afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  setAudioPort(null)
  localStorage.clear()
})

describe('practice room motion and sound (DRAFT-020)', () => {
  it('AC4: Start unlocks the audio from the click', async () => {
    await startDraft('Untimed')
    await screen.findByText('Current bid')
    expect(unlocked).toBeGreaterThan(0)
  })

  it('AC2: the ring closes with the time and turns urgent at 5 s', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await startDraft('Real timers')
    await screen.findByText('Current bid')
    const ring = await screen.findByTestId('clock-ring')
    expect(ring).toHaveAttribute('data-phase', 'calm')
    expect(ring).toHaveTextContent(/^\d+ seconds$/)
    await act(async () => {
      vi.advanceTimersByTime(10_500)
    })
    const warn = screen.getByTestId('clock-ring')
    expect(warn).toHaveAttribute('data-phase', 'warn')
    expect(Number.parseInt(warn.textContent ?? '', 10)).toBeLessThanOrEqual(10)
    await act(async () => {
      vi.advanceTimersByTime(5_000)
    })
    const urgent = screen.getByTestId('clock-ring')
    expect(urgent).toHaveAttribute('data-phase', 'urgent')
    expect(Number.parseInt(urgent.textContent ?? '', 10)).toBeLessThanOrEqual(5)
  })

  it('AC2: with reduced motion the ring steps once a second instead of animating', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    localStorage.setItem(FX_KEY, JSON.stringify({ reduceMotion: true }))
    const raf = vi.spyOn(window, 'requestAnimationFrame')
    await startDraft('Real timers')
    await screen.findByText('Current bid')
    const arc = (await screen.findByTestId('clock-ring')).querySelectorAll('circle')[1]
    const offset = () => arc?.style.strokeDashoffset
    const first = offset()
    await act(async () => {
      vi.advanceTimersByTime(300)
    })
    expect(offset()).toBe(first)
    await act(async () => {
      vi.advanceTimersByTime(1_200)
    })
    expect(offset()).not.toBe(first)
    expect(raf).not.toHaveBeenCalled()
  })

  it('AC3: a bid plays the bid cue', async () => {
    await startDraft('Untimed')
    const place = (await screen.findAllByRole('button', { name: /^Bid \$\d+$/ }))[0] as HTMLElement
    played.length = 0
    await act(async () => {
      fireEvent.click(place)
    })
    await waitFor(() => expect(played).toContain('bid'))
  })

  it('AC3: sounds follow the draft; fast-forward does not flood', async () => {
    await startDraft('Untimed')
    fireEvent.click(await screen.findByRole('button', { name: /Pass/ }))
    await act(async () => {})
    await waitFor(() => expect(played).toContain('soldOther'))
    played.length = 0
    fireEvent.click(await screen.findByRole('button', { name: 'Sim the rest' }))
    await screen.findByText('Practice draft complete', undefined, { timeout: 20_000 })
    expect(played.filter((c) => c === 'soldOther' || c === 'soldYou')).toHaveLength(0)
    expect(played).toContain('done')
  }, 30_000)

  it('AC3: an expired clock plays the expire cue', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await startDraft('Real timers')
    await screen.findByText('Current bid')
    await act(async () => {
      vi.advanceTimersByTime(21_000)
    })
    expect(played).toContain('expire')
  })

  it('AC4: mute persists and silences the room', async () => {
    await startDraft('Untimed')
    fireEvent.click(await screen.findByRole('button', { name: 'Sound: on' }))
    expect(JSON.parse(localStorage.getItem(FX_KEY) ?? '{}')).toMatchObject({ muted: true })
    played.length = 0
    fireEvent.click(await screen.findByRole('button', { name: /Pass/ }))
    await act(async () => {})
    expect(played).toEqual([])
  })

  it('AC4: the hint clears by itself when the context resumes after Start', async () => {
    status = 'suspended'
    port.unlock = () => Promise.resolve('suspended')
    await startDraft('Untimed')
    await screen.findByRole('button', { name: /tap to enable/ })
    await act(async () => {
      setStatus('running')
    })
    expect(screen.queryByRole('button', { name: /tap to enable/ })).toBeNull()
  })

  it('AC4: a suspended context shows the enable hint, and tapping it unlocks', async () => {
    status = 'suspended'
    port.unlock = () => {
      status = 'suspended'
      return Promise.resolve('suspended')
    }
    await startDraft('Untimed')
    const hint = await screen.findByRole('button', { name: /tap to enable/ })
    port.unlock = defaultUnlock
    await act(async () => {
      fireEvent.click(hint)
    })
    expect(screen.queryByRole('button', { name: /tap to enable/ })).toBeNull()
  })
})
