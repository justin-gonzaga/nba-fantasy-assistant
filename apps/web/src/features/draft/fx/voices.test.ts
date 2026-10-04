import { MAX_CUE_SECONDS, VOICES, cueLength, type Cue } from './voices'

describe('voices (DRAFT-020 AC5)', () => {
  const cues = Object.keys(VOICES) as Cue[]

  it('has every cue of the design table', () => {
    expect([...cues].sort()).toEqual(
      [
        'bid',
        'done',
        'expire',
        'nominate',
        'outbid',
        'soldOther',
        'soldYou',
        'tick',
        'tickUrgent',
      ].sort(),
    )
  })

  it.each(cues)('%s: finite, positive and no longer than the cap', (cue) => {
    expect(VOICES[cue].length).toBeGreaterThan(0)
    for (const n of VOICES[cue]) {
      expect(Number.isFinite(n.freq) && n.freq > 0).toBe(true)
      expect(Number.isFinite(n.start) && n.start >= 0).toBe(true)
      expect(Number.isFinite(n.dur) && n.dur > 0).toBe(true)
      expect(n.gain).toBeGreaterThan(0)
      expect(n.gain).toBeLessThanOrEqual(1)
      if (n.to !== undefined) expect(n.to).toBeGreaterThan(0)
    }
    expect(cueLength(cue)).toBeLessThanOrEqual(MAX_CUE_SECONDS)
  })
})
