import { samplePlayers } from '../../src/api/fixtures'
import type { PlayerBadge, PlayerRow, Players } from '../../src/api/types'

// WEB-008: a realistic draft-day payload, 589 rows like the real pre-season pool. The first ten are
// the app's SAMPLE players (Jokić, Wembanyama, …); the rest are fictional, generated from a fixed
// seed so every run sees the same list. Typed against the API contract (src/api/types.ts).

export const PLAYER_COUNT = 589

const FIRST = ['Marcus', 'Devin', 'Tyrese', 'Jalen', 'Isaiah', 'Caleb', 'Aaron', 'Miles', 'Andre']
const LAST = ['Okafor', 'Bridges', 'Hart', 'Lindqvist', 'Moreau', 'Achebe', 'Castillo', 'Novak']
const TEAMS = ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND']
const POSITIONS = ['G', 'F', 'C', 'G-F', 'F-C', 'F-G', 'C-F']
const CATS = ['fg_pct', 'ft_pct', 'fg3m', 'pts', 'reb', 'ast', 'stl', 'blk', 'tov']

/** mulberry32: a tiny seeded PRNG, so the payload is identical on every run. */
function rng(seed: number) {
  let a = seed
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const badge = (
  code: PlayerBadge['code'],
  label: string,
  tone: PlayerBadge['tone'],
  why: string,
): PlayerBadge => ({ code, label, tone, why })

const tierOf = (rank: number) => (rank <= 12 ? 1 : rank <= 36 ? 2 : rank <= 80 ? 3 : 4)

function generated(rank: number, rand: () => number): PlayerRow {
  const i = rank - 11
  const name = `${FIRST[i % FIRST.length]} ${LAST[Math.floor(i / FIRST.length) % LAST.length]} ${
    Math.floor(i / (FIRST.length * LAST.length)) + 1
  }`.replace(/ 1$/, '')
  const dollars = Math.max(0, Math.round(42 * Math.exp(-(rank - 10) / 45)))
  const strengths = Object.fromEntries(
    CATS.map((c) => [c, Math.round((rand() * 3 - 1.2) * 100) / 100]),
  )
  const status = rank % 53 === 0 ? 'Out' : rank % 29 === 0 ? 'Questionable' : null
  const badges: PlayerBadge[] = [
    ...(status ? [badge('injured_today', status, 'warn', `${status} on today's report`)] : []),
    ...(rank % 23 === 0
      ? [
          badge(
            'injury_prone',
            'Injury prone',
            'lose',
            `Played ${40 + (rank % 20)}, ${30 + (rank % 15)} and ${50 + (rank % 10)} of 82 games in the last three seasons`,
          ),
        ]
      : []),
    ...(rank % 31 === 0
      ? [
          badge(
            'missed_time',
            'Missed time',
            'warn',
            `Played ${20 + (rank % 30)} of 82 games last season`,
          ),
        ]
      : []),
    ...(rank % 37 === 0
      ? [badge('breakout', 'Breakout chance', 'accent', 'Breakout chance 27 % (top 20 %)')]
      : []),
    ...(rank % 41 === 0
      ? [badge('bounce_back', 'Bounce-back', 'win', 'Bounce-back chance 33 % (top 20 %)')]
      : []),
    ...(rank % 17 === 0 ? [badge('rookie', 'Rookie', 'neutral', 'First NBA season')] : []),
    ...(tierOf(rank) === 1
      ? [badge('top_tier', 'Top tier', 'accent', 'Tier 1 of 4 for this strategy')]
      : []),
  ]
  const r = (lo: number, hi: number) => Math.round((lo + rand() * (hi - lo)) * 10) / 10
  return {
    id: 2_000_000 + rank,
    name,
    team: TEAMS[rank % TEAMS.length] ?? null,
    positions: POSITIONS[rank % POSITIONS.length] ?? null,
    rank,
    tier: tierOf(rank),
    dollars,
    value: Math.round(Object.values(strengths).reduce((a, b) => a + b, 0) * 1000) / 1000,
    inPool: rank <= 156,
    status,
    strengths,
    projection:
      rank % 97 === 0
        ? null
        : {
            games: r(45, 78),
            mpg: r(12, 34),
            pts: r(4, 22),
            reb: r(1.5, 9),
            ast: r(0.5, 6),
            stl: r(0.2, 1.4),
            blk: r(0.1, 1.5),
            fg3m: r(0, 2.8),
            tov: r(0.5, 2.6),
            fgPct: 0.44 + rand() * 0.1,
            ftPct: 0.68 + rand() * 0.2,
          },
    badges,
  }
}

/** Healthy rank (WEB-019): the order if everyone played 72 games — the injured climb. */
function withHealthyRank(rows: PlayerRow[]): PlayerRow[] {
  const bump = (p: PlayerRow) =>
    p.badges?.some((b) => b.code === 'missed_time')
      ? 40
      : p.badges?.some((b) => b.code === 'injury_prone')
        ? 15
        : 0
  const order = [...rows].sort(
    (a, b) => b.dollars + bump(b) - (a.dollars + bump(a)) || a.rank - b.rank,
  )
  const healthy = new Map(order.map((p, i) => [p.id, i + 1]))
  return rows.map((p) => ({ ...p, healthyRank: healthy.get(p.id) ?? null }))
}

function buildRows(): PlayerRow[] {
  const rand = rng(589)
  const rows: PlayerRow[] = [...samplePlayers.players]
  for (let rank = rows.length + 1; rank <= PLAYER_COUNT; rank++) rows.push(generated(rank, rand))
  return withHealthyRank(rows)
}

const rows = buildRows()

/** The draft payload under a strategy: punts re-rank by dropping that category's strength. */
export function draftPlayers(variant = 'all'): Players {
  if (variant === 'all') return { ...samplePlayers, players: rows, badgeNotes: [] }
  const cat = variant.replace(/^punt_/, '')
  const score = (p: PlayerRow) => p.value - (p.strengths[cat] ?? 0)
  const players = [...rows]
    .sort((a, b) => score(b) - score(a))
    .map((p, i) => ({ ...p, rank: i + 1 }))
  return { ...samplePlayers, variant, players, badgeNotes: [] }
}

/** The player the healthy-rank sort puts first. */
export const healthiestFirst: PlayerRow = (() => {
  const p = rows.find((r) => r.healthyRank === 1)
  if (!p) throw new Error('no healthy rank 1 in the fixture')
  return p
})()
