// WEB-020: decision indicators — pure helpers for the Players page.
import type { PlayerRow } from '../../api/types'

export type PlayerIndicator = NonNullable<PlayerRow['indicators']>[number]
export type SignalCode = 'bigger_role' | 'high_certainty' | 'steady'

export const SIGNAL_FILTERS: [SignalCode, string][] = [
  ['bigger_role', 'Bigger role'],
  ['high_certainty', 'High certainty'],
  ['steady', 'Steady'],
]

export const INDICATOR_SORTS: [string, string][] = [
  ['certainty', 'Certainty'],
  ['role', 'Role change'],
]

const find = (p: PlayerRow, code: PlayerIndicator['code']) =>
  (p.indicators ?? []).find((i) => i.code === code)

export function hasIndicators(players: PlayerRow[] | undefined): boolean {
  return (players ?? []).some((p) => (p.indicators ?? []).length > 0)
}

const MATCH: Record<SignalCode, (p: PlayerRow) => boolean> = {
  bigger_role: (p) => (find(p, 'role')?.value ?? 0) > 0,
  high_certainty: (p) => find(p, 'certainty')?.label === 'High certainty',
  steady: (p) => find(p, 'consistency')?.label === 'Steady',
}

/** Any of the chosen signals (empty = no filter). */
export function hasAnySignal(p: PlayerRow, chosen: SignalCode[]): boolean {
  return chosen.length === 0 || chosen.some((c) => MATCH[c](p))
}

export function parseSignalParam(value: string | null): SignalCode[] {
  const known = new Set(SIGNAL_FILTERS.map(([c]) => c))
  return (value ?? '').split(',').filter((c): c is SignalCode => known.has(c as SignalCode))
}

/** Sort keys: certainty ascending spread (surest first); role change descending. */
export function indicatorKey(p: PlayerRow, sort: string): number {
  if (sort === 'certainty') return -(find(p, 'certainty')?.value ?? Infinity)
  return find(p, 'role')?.value ?? -Infinity
}
