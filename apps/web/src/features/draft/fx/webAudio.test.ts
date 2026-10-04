import { silentPort, webAudioPort } from './audio'
import { VOICES } from './voices'

type Param = {
  value: number
  setValueAtTime: ReturnType<typeof vi.fn>
  exponentialRampToValueAtTime: ReturnType<typeof vi.fn>
}
const param = (): Param => ({
  value: 1,
  setValueAtTime: vi.fn(),
  exponentialRampToValueAtTime: vi.fn(),
})

type FakeOsc = {
  type: string
  frequency: Param
  connect: ReturnType<typeof vi.fn>
  disconnect: ReturnType<typeof vi.fn>
  start: ReturnType<typeof vi.fn>
  stop: ReturnType<typeof vi.fn>
  onended: (() => void) | null
}
type FakeGain = {
  gain: Param
  connect: ReturnType<typeof vi.fn>
  disconnect: ReturnType<typeof vi.fn>
}

let made: FakeCtx[] = []
let resumeFails = false

class FakeCtx {
  state: 'suspended' | 'running' = 'suspended'
  onstatechange: (() => void) | null = null
  currentTime = 1
  destination = {}
  oscillators: FakeOsc[] = []
  gains: FakeGain[] = []
  constructor() {
    made.push(this)
  }
  resume() {
    if (resumeFails) return Promise.reject(new Error('blocked'))
    this.state = 'running'
    this.onstatechange?.()
    return Promise.resolve()
  }
  createGain() {
    const g: FakeGain = { gain: param(), connect: vi.fn(), disconnect: vi.fn() }
    this.gains.push(g)
    return g
  }
  createOscillator() {
    const o: FakeOsc = {
      type: '',
      frequency: param(),
      connect: vi.fn(),
      disconnect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
      onended: null,
    }
    this.oscillators.push(o)
    return o
  }
}
const Ctor = FakeCtx as unknown as new () => AudioContext

beforeEach(() => {
  made = []
  resumeFails = false
})

describe('Web Audio adapter (DRAFT-020 AC5)', () => {
  it('tells subscribers when the context changes state, and stops after unsubscribe', async () => {
    const p = webAudioPort(Ctor)
    const seen: string[] = []
    const off = p.subscribe(() => seen.push(p.status()))
    await p.unlock()
    expect(seen).toContain('running')
    off()
    const n = seen.length
    made[0]?.onstatechange?.()
    expect(seen).toHaveLength(n)
  })

  it('is unavailable without an AudioContext; the silent port does nothing', async () => {
    const p = webAudioPort(undefined)
    expect(p.status()).toBe('unavailable')
    expect(await p.unlock()).toBe('unavailable')
    p.play('tick')
    expect(await silentPort().unlock()).toBe('unavailable')
  })

  it('creates no context until unlock, then plays one oscillator per note', async () => {
    const p = webAudioPort(Ctor)
    expect(p.status()).toBe('suspended')
    p.play('soldYou')
    expect(made).toHaveLength(0)
    expect(await p.unlock()).toBe('running')
    p.play('soldYou')
    const ctx = made[0] as FakeCtx
    expect(ctx.oscillators).toHaveLength(VOICES.soldYou.length)
    for (const o of ctx.oscillators) {
      expect(o.start).toHaveBeenCalledTimes(1)
      expect(o.stop).toHaveBeenCalledTimes(1)
    }
  })

  it('disconnects every node when a note ends', async () => {
    const p = webAudioPort(Ctor)
    await p.unlock()
    p.play('nominate')
    const ctx = made[0] as FakeCtx
    for (const o of ctx.oscillators) o.onended?.()
    for (const o of ctx.oscillators) expect(o.disconnect).toHaveBeenCalled()
    // gains[0] is the master; each note has its own gain
    for (const g of ctx.gains.slice(1)) expect(g.disconnect).toHaveBeenCalled()
  })

  it('stays suspended, without throwing, when the browser refuses to resume', async () => {
    resumeFails = true
    const p = webAudioPort(Ctor)
    expect(await p.unlock()).toBe('suspended')
    p.play('bid')
    expect((made[0] as FakeCtx).oscillators).toHaveLength(0)
  })

  it('clamps the volume to [0, 1]', async () => {
    const p = webAudioPort(Ctor)
    await p.unlock()
    const master = (made[0] as FakeCtx).gains[0]
    p.setVolume(3)
    expect(master?.gain.value).toBe(1)
    p.setVolume(-1)
    expect(master?.gain.value).toBe(0)
  })
})
