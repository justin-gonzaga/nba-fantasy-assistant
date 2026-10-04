// SIM-004 AC4: the week's game schedule, from team game dates. A player who sat out (injury, rest) still has
// a game that day, exactly as a manager would have seen it beforehand; only box scores tell who played.
// Projections use only games before the week (point-in-time).

import type { Line } from './matchup'
import type { Season } from './season'

/** The team (id) a player is with on `date`: his latest game before it, else his first game's team. */
export function teamOn(s: Season, pid: number, date: string): number | null {
  const games = s.games.get(pid)
  if (!games?.length) return null
  let team = games[0]?.team ?? null
  for (const g of games) {
    if (g.date >= date) break
    team = g.team
  }
  return team
}

/** Whether a player has a game that day: his team plays (whether or not he does), or he played. */
export function hasGame(s: Season, pid: number, date: string): boolean {
  if (s.lines.get(date)?.has(pid)) return true
  const team = teamOn(s, pid, date)
  return team !== null && (s.teamDays.get(date)?.has(team) ?? false)
}

export function gamesInWeek(s: Season, pid: number, days: readonly string[]): number {
  return days.reduce((n, d) => n + (hasGame(s, pid, d) ? 1 : 0), 0)
}

/** NBA team id → its abbreviation, from the players' opening teams (the most common pairing wins). */
export function teamNames(s: Season): Map<number, string> {
  const votes = new Map<number, Map<string, number>>()
  for (const p of s.players.values()) {
    const first = s.games.get(p.id)?.[0]
    if (!first || !p.team) continue
    const v = votes.get(first.team) ?? new Map<string, number>()
    v.set(p.team, (v.get(p.team) ?? 0) + 1)
    votes.set(first.team, v)
  }
  const out = new Map<number, string>()
  for (const [id, v] of votes)
    out.set(
      id,
      [...v.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0] ?? '',
    )
  return out
}

/** Games per NBA team this week (some play 4, some 2): the streaming picture. */
export function teamGamesInWeek(s: Season, days: readonly string[]): Map<number, number> {
  const out = new Map<number, number>()
  for (const d of days) for (const t of s.teamDays.get(d) ?? []) out.set(t, (out.get(t) ?? 0) + 1)
  return out
}

const KEYS = ['pts', 'reb', 'ast', 'stl', 'blk', 'fg3m', 'tov', 'fgm', 'fga', 'ftm', 'fta'] as const

/** A player's per-game averages over his games before `before`; null with none. */
export function averagesBefore(s: Season, pid: number, before: string): Line | null {
  const sum = Object.fromEntries(KEYS.map((k) => [k, 0])) as Line
  let n = 0
  for (const g of s.games.get(pid) ?? []) {
    if (g.date >= before) break
    const line = s.lines.get(g.date)?.get(pid)
    if (!line) continue
    for (const k of KEYS) sum[k] += line[k]
    n += 1
  }
  if (n === 0) return null
  for (const k of KEYS) sum[k] /= n
  return sum
}

/**
 * Expected lines for the week, known before it starts: each player's averages before the week on each day he
 * has a game. Fed to `playWeek` in place of the real lines, it gives the projected category picture.
 */
export function projectedLines(
  s: Season,
  pids: Iterable<number>,
  days: readonly string[],
): Map<string, Map<number, Line>> {
  const out = new Map<string, Map<number, Line>>(days.map((d) => [d, new Map()]))
  const start = days[0] ?? ''
  for (const pid of pids) {
    const avg = averagesBefore(s, pid, start)
    if (!avg) continue
    for (const d of days) if (hasGame(s, pid, d)) out.get(d)?.set(pid, avg)
  }
  return out
}
