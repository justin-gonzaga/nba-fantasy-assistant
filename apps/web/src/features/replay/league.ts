// SIM-002/004: the league a replay draft produced, kept in this browser (one at a time) so the season can
// be played week by week. Practice data: never sent anywhere.

import type { Sale } from '../draft/live'

export type WeekRecord = { opponent: string; wins: number; losses: number; ties: number }

export type ReplayLeague = {
  version: 1
  season: string
  me: string
  /** team → player ids, in draft order */
  rosters: Record<string, number[]>
  savedAt: string
  /** week number → my kept result that week (SIM-004 "Keep") */
  results: Record<string, WeekRecord>
}

const KEY = 'replay-league'

export function leagueFromSales(
  season: string,
  teams: readonly string[],
  me: string,
  sales: readonly Sale[],
  savedAt: string,
): ReplayLeague {
  const rosters: Record<string, number[]> = Object.fromEntries(teams.map((t) => [t, []]))
  for (const s of sales) rosters[s.team]?.push(Number(s.pid))
  return { version: 1, season, me, rosters, savedAt, results: {} }
}

function valid(x: unknown): x is ReplayLeague {
  if (typeof x !== 'object' || x === null) return false
  const l = x as Partial<ReplayLeague>
  return (
    l.version === 1 &&
    typeof l.season === 'string' &&
    typeof l.me === 'string' &&
    typeof l.rosters === 'object' &&
    l.rosters !== null &&
    Object.values(l.rosters).every((r) => Array.isArray(r) && r.every(Number.isInteger)) &&
    typeof l.results === 'object' &&
    l.results !== null
  )
}

export function loadLeague(storage: Pick<Storage, 'getItem'> = localStorage): ReplayLeague | null {
  try {
    const raw = storage.getItem(KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : null
    return valid(parsed) ? parsed : null
  } catch {
    return null // storage blocked or a corrupt entry: as if none was saved
  }
}

export function saveLeague(
  league: ReplayLeague,
  storage: Pick<Storage, 'setItem'> = localStorage,
): void {
  try {
    storage.setItem(KEY, JSON.stringify(league))
  } catch {
    // storage full or blocked: the season can't be kept, but the draft report still shows
  }
}
