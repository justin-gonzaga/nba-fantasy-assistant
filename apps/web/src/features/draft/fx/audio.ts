import { VOICES, type Cue } from './voices'

export type AudioStatus = 'running' | 'suspended' | 'unavailable'

/** What the room needs from audio; a silent fake stands in for it in tests. */
export interface AudioPort {
  play(cue: Cue): void
  setVolume(volume: number): void
  /** Call inside a click: browsers only start audio after a gesture. Resolves to the new status. */
  unlock(): Promise<AudioStatus>
  status(): AudioStatus
  /** Calls `fn` whenever the status may have changed (context state change, unlock); returns an unsubscribe. */
  subscribe(fn: () => void): () => void
}

export function silentPort(): AudioPort {
  return {
    play: () => {},
    setVolume: () => {},
    unlock: () => Promise.resolve('unavailable'),
    status: () => 'unavailable',
    subscribe: () => () => {},
  }
}

type ContextClass = new () => AudioContext

/** Web Audio adapter: each note is a short oscillator + gain envelope, disconnected when it ends. */
export function webAudioPort(Ctor: ContextClass | undefined): AudioPort {
  let ctx: AudioContext | null = null
  let master: GainNode | null = null
  let volume = 0.6
  const listeners = new Set<() => void>()
  const notify = () => listeners.forEach((fn) => fn())

  const context = () => {
    if (!ctx && Ctor) {
      ctx = new Ctor()
      ctx.onstatechange = notify
      master = ctx.createGain()
      master.gain.value = volume
      master.connect(ctx.destination)
    }
    return ctx
  }
  const status = (): AudioStatus => {
    if (!ctx) return Ctor ? 'suspended' : 'unavailable'
    return ctx.state === 'running' ? 'running' : 'suspended'
  }

  return {
    status,
    subscribe(fn) {
      listeners.add(fn)
      return () => void listeners.delete(fn)
    },
    setVolume(v) {
      volume = Math.min(1, Math.max(0, v))
      if (master) master.gain.value = volume
    },
    async unlock() {
      const c = context()
      if (!c) return 'unavailable'
      try {
        if (c.state !== 'running') await c.resume()
      } catch {
        // stays suspended; the room shows the enable hint
      }
      notify()
      return status()
    },
    play(cue) {
      const c = ctx
      if (!c || !master || c.state !== 'running') return
      const t0 = c.currentTime
      for (const n of VOICES[cue]) {
        const osc = c.createOscillator()
        const env = c.createGain()
        const t = t0 + n.start
        osc.type = n.type
        osc.frequency.setValueAtTime(n.freq, t)
        if (n.to) osc.frequency.exponentialRampToValueAtTime(n.to, t + n.dur)
        env.gain.setValueAtTime(0.0001, t)
        env.gain.exponentialRampToValueAtTime(n.gain, t + 0.006)
        env.gain.exponentialRampToValueAtTime(0.0001, t + n.dur)
        osc.connect(env)
        env.connect(master)
        osc.onended = () => {
          osc.disconnect()
          env.disconnect()
        }
        osc.start(t)
        osc.stop(t + n.dur + 0.02)
      }
    },
  }
}

let shared: AudioPort | null = null

/** The page-wide port (one AudioContext). Tests swap it with `setAudioPort`. */
export function audioPort(): AudioPort {
  shared ??= webAudioPort(
    typeof window === 'undefined'
      ? undefined
      : (window.AudioContext ??
          (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext),
  )
  return shared
}

export function setAudioPort(port: AudioPort | null): void {
  shared = port
}
