export type ClockPhase = 'calm' | 'warn' | 'urgent' | 'expired'

export const WARN_AT = 10
export const URGENT_AT = 5

/** The ring's fill (1 = full) and the colour phase for `left` whole seconds of `total`. */
export function clockState(left: number, total: number): { fraction: number; phase: ClockPhase } {
  const fraction = total > 0 ? Math.min(1, Math.max(0, left / total)) : 0
  const phase: ClockPhase =
    left <= 0 ? 'expired' : left <= URGENT_AT ? 'urgent' : left <= WARN_AT ? 'warn' : 'calm'
  return { fraction, phase }
}
