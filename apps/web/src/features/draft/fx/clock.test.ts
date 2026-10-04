import { clockState, URGENT_AT, WARN_AT } from './clock'

describe('clockState phases and fraction (DRAFT-020 AC1)', () => {
  it.each([
    [30, 30, 1, 'calm'],
    [11, 30, 11 / 30, 'calm'],
    [10, 30, 10 / 30, 'warn'],
    [6, 30, 6 / 30, 'warn'],
    [5, 30, 5 / 30, 'urgent'],
    [1, 30, 1 / 30, 'urgent'],
    [0, 30, 0, 'expired'],
  ])('left %i of %i', (left, total, fraction, phase) => {
    const s = clockState(left, total)
    expect(s.fraction).toBeCloseTo(fraction)
    expect(s.phase).toBe(phase)
  })

  it('keeps the fraction inside [0, 1] for out-of-range input', () => {
    for (const [left, total] of [
      [-3, 30],
      [45, 30],
      [5, 0],
      [0, 0],
    ] as const) {
      const f = clockState(left, total).fraction
      expect(f).toBeGreaterThanOrEqual(0)
      expect(f).toBeLessThanOrEqual(1)
    }
  })

  it('names the thresholds', () => {
    expect([WARN_AT, URGENT_AT]).toEqual([10, 5])
  })
})
