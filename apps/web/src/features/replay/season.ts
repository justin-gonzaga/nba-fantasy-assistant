// SIM-002: a published season replay file (SIM-001, `GET /replay/{season}`) as the draft room and the
// matchup simulator use it. The draft sees only the file's pre-season values (leak-free by construction:
// computed from earlier seasons); the game lines are for scoring weeks, never shown before they happen.

import type { DraftPlayer } from '../draft/live'
import type { Line, ReplayPlayer } from './matchup'

export const REPLAY_SEASONS = ['2023-24', '2024-25', '2025-26'] as const // G-31 Q5 A

const STATS = [
  'pts',
  'reb',
  'ast',
  'stl',
  'blk',
  'fg3m',
  'tov',
  'fgm',
  'fga',
  'ftm',
  'fta',
] as const

export type ReplayWeek = { week: number; start: string; end: string }

export type ReplayDoc = {
  season: string
  method: string
  players: ReplayPlayer[]
  weeks: ReplayWeek[]
  lines: {
    dates: string[]
    players: number[]
    day: number[]
    min: number[]
    team?: number[]
  } & Record<(typeof STATS)[number], number[]>
}

export type Season = {
  season: string
  players: Map<number, ReplayPlayer>
  weeks: ReplayWeek[]
  /** ISO date → player id → that day's line (players who played). */
  lines: Map<string, Map<number, Line>>
  /** ISO date → the NBA teams (ids) that played that day: the schedule, known in advance. */
  teamDays: Map<string, Set<number>>
  /** player → his games in date order, with the team he played for. */
  games: Map<number, { date: string; team: number }[]>
}

export function parseSeason(doc: ReplayDoc): Season {
  const players = new Map(doc.players.map((p) => [p.id, p]))
  const lines = new Map<string, Map<number, Line>>()
  const teamDays = new Map<string, Set<number>>()
  const games = new Map<number, { date: string; team: number }[]>()
  const L = doc.lines
  for (let i = 0; i < L.players.length; i++) {
    const date = L.dates[L.day[i] ?? -1]
    const pid = L.players[i]
    if (date === undefined || pid === undefined) continue
    let day = lines.get(date)
    if (!day) lines.set(date, (day = new Map()))
    const line = {} as Line
    for (const s of STATS) line[s] = L[s][i] ?? 0
    day.set(pid, line)
    const team = L.team?.[i]
    if (team !== undefined) {
      let teams = teamDays.get(date)
      if (!teams) teamDays.set(date, (teams = new Set()))
      teams.add(team)
      let mine = games.get(pid)
      if (!mine) games.set(pid, (mine = []))
      mine.push({ date, team })
    }
  }
  return { season: doc.season, players, weeks: doc.weeks, lines, teamDays, games }
}

/** The draft pool: the valued players, best first, as the room's engine takes them. */
export function draftPool(s: Season): DraftPlayer[] {
  return [...s.players.values()]
    .filter((p) => p.rank !== null && p.usd > 0)
    .sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0))
    .map((p) => ({ id: String(p.id), usd: p.usd, z: p.z }))
}

/** Every calendar date of a week, start to end inclusive (lineups are daily, games or not). */
export function weekDays(w: ReplayWeek): string[] {
  const out: string[] = []
  const end = Date.parse(`${w.end}T00:00:00Z`)
  for (let t = Date.parse(`${w.start}T00:00:00Z`); t <= end; t += 86_400_000)
    out.push(new Date(t).toISOString().slice(0, 10))
  return out
}
