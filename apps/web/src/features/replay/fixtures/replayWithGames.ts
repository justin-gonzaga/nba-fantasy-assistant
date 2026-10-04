import values from '../../draft/fixtures/values-2026-27.json' with { type: 'json' }
import { leagueFromSales, type ReplayLeague } from '../league'
import type { ReplayDoc } from '../season'

const POS = ['G', 'F', 'C', 'G-F', 'F-C', 'G'] as const
const DAYS = [
  '2024-10-22', // Tue: week 1 runs Tue-Sun
  '2024-10-23',
  '2024-10-24',
  '2024-10-25',
  '2024-10-26',
  '2024-10-27',
  '2024-10-28', // Mon: week 2
  '2024-10-29',
  '2024-10-30',
  '2024-10-31',
  '2024-11-01',
  '2024-11-02',
  '2024-11-03',
]
const TEAMS = 30

/**
 * Two weeks of a season over the 2026-27 values fixture (224 valued players) plus 40 unvalued ones. Team t
 * plays on day d when (t + d) is even (3-4 games a week). Every 7th player sits out his team's second game
 * (a DNP). Lines are deterministic.
 */
export function replayWithGames(season = '2024-25'): ReplayDoc {
  const valued = values.players.map((v, i) => ({
    id: Number(v.id),
    name: `Replay ${v.id}`,
    team: `T${i % TEAMS}`,
    pos: POS[i % POS.length] ?? 'G',
    usd: v.usd,
    rank: (i + 1) as number | null,
    z: v.z,
  }))
  const extra = Array.from({ length: 40 }, (_, k) => ({
    id: 900_000 + k,
    name: `Free ${k}`,
    team: `T${k % TEAMS}`,
    pos: POS[k % POS.length] ?? 'G',
    usd: 0,
    rank: null as number | null,
    z: [0, 0, 0, 0, 0, 0, 0, 0, 0],
  }))
  const players = [...valued, ...extra]
  const cols = {
    dates: DAYS,
    players: [] as number[],
    day: [] as number[],
    team: [] as number[],
    min: [] as number[],
    pts: [] as number[],
    reb: [] as number[],
    ast: [] as number[],
    stl: [] as number[],
    blk: [] as number[],
    fg3m: [] as number[],
    tov: [] as number[],
    fgm: [] as number[],
    fga: [] as number[],
    ftm: [] as number[],
    fta: [] as number[],
  }
  DAYS.forEach((_, d) => {
    players.forEach((p, i) => {
      const t = i % TEAMS
      if ((t + d) % 2 !== 0) return
      const nth = Math.floor(d / 2)
      if (i % 7 === 0 && nth === 1) return // DNP: his team plays, he doesn't
      const k = (i * 7 + d * 3) % 20
      cols.players.push(p.id)
      cols.day.push(d)
      cols.team.push(t)
      cols.min.push(20 + k)
      cols.pts.push(5 + k)
      cols.reb.push(2 + (k % 9))
      cols.ast.push(1 + (k % 7))
      cols.stl.push(k % 3)
      cols.blk.push(k % 2)
      cols.fg3m.push(k % 4)
      cols.tov.push(1 + (k % 4))
      cols.fgm.push(2 + (k % 8))
      cols.fga.push(6 + (k % 10))
      cols.ftm.push(k % 5)
      cols.fta.push((k % 5) + 1)
    })
  })
  return {
    season,
    method: 'ours',
    players,
    weeks: [
      { week: 1, start: '2024-10-22', end: '2024-10-27' },
      { week: 2, start: '2024-10-28', end: '2024-11-03' },
    ],
    lines: cols,
  }
}

/** A drafted league: the 224 valued players dealt in a snake to 16 teams (me first). */
export function draftedLeague(season = '2024-25'): ReplayLeague {
  const teams = ['me', ...Array.from({ length: 15 }, (_, i) => `Team ${i + 2}`)]
  const sales = values.players.slice(0, 16 * 14).map((v, i) => {
    const round = Math.floor(i / 16)
    const pick = i % 16
    const team = teams[round % 2 === 0 ? pick : 15 - pick] ?? 'me'
    return { pid: v.id, team, price: 1 }
  })
  return leagueFromSales(season, teams, 'me', sales, '2026-10-04T00:00:00Z')
}
