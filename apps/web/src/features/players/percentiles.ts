// WEB-025: where a player sits in each category against the expected draft pool (design-language §9).
import type { PlayerRow } from '../../api/types'
import { CATEGORIES, inRotation } from './format'

/** Fewer in-pool players than this and a percentile says little; the bars are hidden. */
export const MIN_POOL = 20

export type CategoryPercentile = { key: string; label: string; percentile: number }

/**
 * Percentile 0–100 of the player's category strength among in-pool rotation players (share at or below).
 * Strengths are already signed so + helps your team, which makes TOV "higher = fewer turnovers".
 * Returns null when the pool is too small to rank against.
 */
export function categoryPercentiles(
  player: PlayerRow,
  players: readonly PlayerRow[],
): CategoryPercentile[] | null {
  const pool = players.filter((p) => p.inPool && inRotation(p)) // WEB-027
  if (pool.length < MIN_POOL) return null
  return CATEGORIES.map(([key, label]) => {
    const mine = player.strengths[key] ?? 0
    const below = pool.filter((p) => (p.strengths[key] ?? 0) <= mine).length
    return { key, label, percentile: Math.round((below / pool.length) * 100) }
  })
}
