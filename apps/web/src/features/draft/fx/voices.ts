export type Cue =
  | 'tick'
  | 'tickUrgent'
  | 'expire'
  | 'nominate'
  | 'bid'
  | 'outbid'
  | 'soldYou'
  | 'soldOther'
  | 'done'

/** One oscillator note: times are seconds from the cue start; `gain` is the peak (0..1). */
export type Note = {
  freq: number
  start: number
  dur: number
  type: OscillatorType
  gain: number
  /** Glide to this frequency by the end of the note. */
  to?: number
}

export const MAX_CUE_SECONDS = 0.6

// Every voice is a few numbers; edit them to change how a cue sounds.
export const VOICES: Record<Cue, Note[]> = {
  tick: [{ freq: 1500, start: 0, dur: 0.04, type: 'square', gain: 0.12 }],
  tickUrgent: [{ freq: 2200, start: 0, dur: 0.05, type: 'square', gain: 0.18 }],
  expire: [{ freq: 130, start: 0, dur: 0.5, type: 'sawtooth', gain: 0.3, to: 90 }],
  nominate: [
    { freq: 660, start: 0, dur: 0.12, type: 'sine', gain: 0.22 },
    { freq: 880, start: 0.1, dur: 0.18, type: 'sine', gain: 0.22 },
  ],
  bid: [{ freq: 1000, start: 0, dur: 0.05, type: 'triangle', gain: 0.25 }],
  outbid: [{ freq: 300, start: 0, dur: 0.14, type: 'triangle', gain: 0.25, to: 220 }],
  soldYou: [
    { freq: 784, start: 0, dur: 0.12, type: 'sine', gain: 0.25 },
    { freq: 1047, start: 0.1, dur: 0.22, type: 'sine', gain: 0.25 },
    { freq: 1568, start: 0.1, dur: 0.22, type: 'sine', gain: 0.1 },
  ],
  soldOther: [{ freq: 180, start: 0, dur: 0.12, type: 'sine', gain: 0.3, to: 110 }],
  done: [
    { freq: 523, start: 0, dur: 0.12, type: 'sine', gain: 0.22 },
    { freq: 659, start: 0.1, dur: 0.12, type: 'sine', gain: 0.22 },
    { freq: 784, start: 0.2, dur: 0.12, type: 'sine', gain: 0.22 },
    { freq: 1047, start: 0.3, dur: 0.3, type: 'sine', gain: 0.22 },
  ],
}

export const cueLength = (cue: Cue) => Math.max(...VOICES[cue].map((n) => n.start + n.dur))
