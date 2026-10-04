// WEB-018: player badges — an icon plus a word, each decided by the API from stored evidence.
import type { PlayerBadge, PlayerRow } from '../../api/types'

export type { PlayerBadge }
export type BadgeCode = PlayerBadge['code']

/** Highest first: a row shows the first ROW_BADGES, then "+N". */
export const PRIORITY: BadgeCode[] = [
  'injured_today',
  'adjusted',
  'injury_prone',
  'missed_time',
  'breakout',
  'bounce_back',
  'rookie',
  'top_tier',
]
export const ROW_BADGES = 2

/** The badges the Players filter offers (URL param `badge`, comma-separated codes). */
export const FILTERS: [BadgeCode, string][] = [
  ['injury_prone', 'Injury prone'],
  ['missed_time', 'Missed time'],
  ['breakout', 'Breakout'],
  ['bounce_back', 'Bounce-back'],
  ['rookie', 'Rookie'],
]

/** A player's badges, highest priority first. */
export function badgesOf(p: PlayerRow): PlayerBadge[] {
  return [...(p.badges ?? [])].sort((a, b) => PRIORITY.indexOf(a.code) - PRIORITY.indexOf(b.code))
}

/** Parses the `badge` URL param into known filter codes. */
export function parseBadgeParam(value: string | null): BadgeCode[] {
  const known = new Set<string>(FILTERS.map(([c]) => c))
  return (value ?? '').split(',').filter((c): c is BadgeCode => known.has(c))
}

/** Whether a player has any of the chosen badges (no choice: everyone). */
export function hasAnyBadge(p: PlayerRow, chosen: BadgeCode[]): boolean {
  return chosen.length === 0 || (p.badges ?? []).some((b) => chosen.includes(b.code))
}
