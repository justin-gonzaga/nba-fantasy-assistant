import { ApiError } from './http'
import type { ApiClient, Matchup, PlayerBadge, PlayerRow, Players, Today, Waivers } from './types'

// SAMPLE data for the demo and tests (D-38): no real league data, other managers as "Team N".
const freshness = {
  asOf: '2026-10-26T09:42:00+11:00',
  sources: [{ name: 'Injury report', asOf: '2026-10-26T09:30:00+11:00' }],
}

export const sampleMatchup: Matchup = {
  weekStart: '2026-10-26',
  weekEnd: '2026-11-01',
  daysLeft: 3,
  opponent: 'Team 7',
  record: { wins: 5, losses: 3, ties: 1 },
  expectedCategories: 5.22,
  categories: [
    {
      code: 'PTS',
      mine: '512',
      theirs: '488',
      winProb: 0.78,
      note: 'Safe unless two starters sit.',
    },
    {
      code: 'REB',
      mine: '201',
      theirs: '214',
      winProb: 0.31,
      note: 'Streaming a big lifts this to about 45%.',
    },
    { code: 'AST', mine: '118', theirs: '102', winProb: 0.82, note: 'Safe.' },
    {
      code: 'STL',
      mine: '34',
      theirs: '31',
      winProb: 0.55,
      note: 'Coin flip; nothing cheap moves it.',
    },
    {
      code: 'BLK',
      mine: '19',
      theirs: '24',
      winProb: 0.28,
      note: 'Adding Jalen Smith (3 games) makes it about even.',
    },
    { code: '3PM', mine: '58', theirs: '49', winProb: 0.8, note: 'Safe.' },
    {
      code: 'FG%',
      mine: '.481',
      theirs: '.466',
      winProb: 0.7,
      note: 'Avoid high-volume poor shooters.',
    },
    {
      code: 'FT%',
      mine: '.792',
      theirs: '.815',
      winProb: 0.3,
      note: 'Hard to flip; do not chase it.',
    },
    {
      code: 'TO',
      mine: '61',
      theirs: '66',
      winProb: 0.68,
      note: 'Fewer is better; you are ahead.',
    },
  ],
  freshness,
}

export const sampleToday: Today = {
  date: '2026-10-26',
  matchup: sampleMatchup,
  freshness,
  actions: [
    {
      id: 'a1',
      kind: 'lineup',
      title: 'Start Keegan Murray over Harrison Barnes',
      detail: 'Barnes has no game today. Murray plays at home.',
      deadline: 'Locks 7:00 pm',
      why: [
        'A player without a game scores nothing today.',
        'About +0.4 expected category wins this week.',
      ],
      confidence: 'high',
      cta: 'Open Yahoo',
    },
    {
      id: 'a2',
      kind: 'injury',
      title: 'Haliburton questionable (hamstring)',
      detail: 'Keep him in; swap in Coby White only if he is ruled out before 6:30 pm.',
      deadline: 'Check 6:30 pm',
      why: [
        'Questionable players played in most comparable past cases (sample).',
        'White has the same game time.',
      ],
      confidence: 'medium',
      cta: 'Remind me',
    },
    {
      id: 'a3',
      kind: 'stream',
      title: 'Add Jalen Smith, drop Cody Martin',
      detail: '3 games this week vs 2. Helps blocks and rebounds.',
      deadline: 'Before tomorrow',
      why: [
        'Blocks: you trail by 1.5 a week; he adds 1.1.',
        'Martin is your lowest-value player this week.',
      ],
      confidence: 'medium',
      cta: 'Open Yahoo',
    },
  ],
}

export const sampleWaivers: Waivers = {
  candidates: [
    {
      id: 'p1',
      name: 'Jalen Smith',
      team: 'CHI',
      positions: 'F-C',
      gamesLeft: 3,
      helps: ['BLK', 'REB'],
      gain: 0.42,
    },
    {
      id: 'p2',
      name: 'Day’Ron Sharpe',
      team: 'BKN',
      positions: 'C',
      gamesLeft: 3,
      helps: ['REB', 'BLK'],
      gain: 0.35,
    },
    {
      id: 'p3',
      name: 'Ayo Dosunmu',
      team: 'CHI',
      positions: 'G',
      gamesLeft: 3,
      helps: ['STL', 'AST'],
      gain: 0.21,
    },
    {
      id: 'p4',
      name: 'Keon Ellis',
      team: 'SAC',
      positions: 'G',
      gamesLeft: 2,
      helps: ['STL', '3PM'],
      gain: 0.18,
    },
    {
      id: 'p5',
      name: 'Precious Achiuwa',
      team: 'NYK',
      positions: 'F-C',
      gamesLeft: 2,
      helps: ['REB'],
      gain: 0.15,
    },
    {
      id: 'p6',
      name: 'Sam Hauser',
      team: 'BOS',
      positions: 'F',
      gamesLeft: 3,
      helps: ['3PM'],
      gain: 0.04,
    },
  ],
  suggestedDrop: 'Cody Martin',
  horizon: 'this week',
  freshness,
}

const CATS = ['fg_pct', 'ft_pct', 'fg3m', 'pts', 'reb', 'ast', 'stl', 'blk', 'tov'] as const

/** A SAMPLE player: values are illustrative, not the model's output. */
function samplePlayer(
  rank: number,
  id: number,
  name: string,
  team: string,
  positions: string,
  dollars: number,
  s: number[],
  line: [number, number, number, number, number, number, number],
  status: string | null = null,
  badges: PlayerBadge[] = [],
): PlayerRow {
  const [pts, reb, ast, stl, blk, fg3m, tov] = line
  const tier = rank <= 3 ? 1 : rank <= 8 ? 2 : 3
  return {
    id,
    name,
    team,
    positions,
    rank,
    tier,
    dollars,
    value: Math.round(s.reduce((a, b) => a + b, 0) * 1000) / 1000,
    inPool: true,
    status,
    strengths: Object.fromEntries(CATS.map((c, i) => [c, s[i] ?? 0])),
    projection: {
      games: 70,
      mpg: 34,
      pts,
      reb,
      ast,
      stl,
      blk,
      fg3m,
      tov,
      fgPct: 0.49,
      ftPct: 0.82,
    },
    // WEB-018: the API's order — today's status first, then the badges given, then top tier.
    badges: [
      ...(status ? [badge('injured_today', status, 'warn', `${status} on today's report`)] : []),
      ...badges,
      ...(tier === 1
        ? [badge('top_tier', 'Top tier', 'accent', 'Tier 1 of 3 for this strategy')]
        : []),
    ],
  }
}

function badge(
  code: PlayerBadge['code'],
  label: string,
  tone: PlayerBadge['tone'],
  why: string,
): PlayerBadge {
  return { code, label, tone, why }
}

const samplePlayerRows: PlayerRow[] = [
  samplePlayer(
    1,
    203999,
    'Nikola Jokić',
    'DEN',
    'C',
    71,
    [2.1, 0.4, 0.3, 1.9, 2.6, 2.8, 1.2, 0.4, -1.4],
    [28, 12.5, 9.8, 1.5, 0.7, 1.2, 3.1],
  ),
  samplePlayer(
    2,
    1641705,
    'Victor Wembanyama',
    'SAS',
    'F-C',
    66,
    [0.3, 0.2, 0.9, 1.5, 1.8, 0.3, 0.9, 4.2, -0.6],
    [25, 11, 3.8, 1.2, 3.6, 2.6, 3.2],
    null,
    [badge('breakout', 'Breakout chance', 'accent', 'Breakout chance 34 % (top 20 %)')],
  ),
  samplePlayer(
    3,
    1628983,
    'Shai Gilgeous-Alexander',
    'OKC',
    'G',
    63,
    [1.2, 1, 0.5, 2.6, -0.2, 0.9, 1.6, 0.5, -0.4],
    [31, 5.3, 6.2, 1.9, 0.9, 1.6, 2.4],
  ),
  samplePlayer(
    4,
    203507,
    'Giannis Antetokounmpo',
    'MIL',
    'F',
    55,
    [1.8, -1.8, -0.9, 2.3, 2, 1.1, 0.6, 0.8, -1],
    [30, 11.8, 6.1, 1, 1.1, 0.4, 3.2],
    'Questionable',
    [badge('missed_time', 'Missed time', 'warn', 'Played 36 of 82 games last season')],
  ),
  samplePlayer(
    5,
    1630162,
    'Anthony Edwards',
    'MIN',
    'G',
    48,
    [-0.2, 0.4, 2.2, 1.9, 0.1, 0.2, 0.7, 0.2, -0.6],
    [27, 5.7, 4.5, 1.3, 0.6, 3.6, 3],
  ),
  samplePlayer(
    6,
    1629029,
    'Luka Dončić',
    'LAL',
    'F-G',
    46,
    [-0.3, -0.1, 1.7, 2.5, 0.7, 2, 0.8, -0.3, -2],
    [29, 8.2, 8.1, 1.6, 0.4, 3.4, 3.9],
  ),
  samplePlayer(
    7,
    1631096,
    'Chet Holmgren',
    'OKC',
    'C-F',
    40,
    [0.8, 0.6, 0.3, 0, 0.9, -0.4, 0.1, 2.9, 0.2],
    [18, 8.5, 2.2, 0.7, 2.4, 1.6, 1.7],
    null,
    [
      badge(
        'injury_prone',
        'Injury prone',
        'lose',
        'Played 82, 32 and 45 of 82 games in the last three seasons',
      ),
      badge('bounce_back', 'Bounce-back', 'win', 'Bounce-back chance 41 % (top 20 %)'),
    ],
  ),
  samplePlayer(
    8,
    1628973,
    'Jalen Brunson',
    'NYK',
    'G',
    33,
    [0.2, 0.8, 0.8, 2, -1, 1.6, -0.3, -0.7, -0.8],
    [26, 3.3, 7.1, 0.9, 0.2, 2.5, 2.6],
  ),
  samplePlayer(
    9,
    1627734,
    'Domantas Sabonis',
    'SAC',
    'F-C',
    30,
    [1.6, -0.3, -0.9, 0.6, 2.9, 1.5, 0.2, -0.3, -1.1],
    [19, 13.4, 6.4, 0.9, 0.4, 0.5, 2.9],
    'Out',
  ),
  samplePlayer(
    10,
    1628369,
    'Jayson Tatum',
    'BOS',
    'F-G',
    4,
    [-0.2, 0.5, 1.5, 1.4, 1, 0.7, 0.4, 0.2, -0.3],
    [26, 8.5, 5.3, 1, 0.5, 3, 2.7],
    'Out',
    [
      badge('missed_time', 'Missed time', 'warn', 'Played 16 of 82 games last season'),
      badge('bounce_back', 'Bounce-back', 'win', 'Bounce-back chance 38 % (top 20 %)'),
    ],
  ),
]

// SAMPLE decision indicators (WEB-020), illustrative only.
const sampleIndicators: Record<number, PlayerRow['indicators']> = {
  1631096: [
    {
      code: 'role',
      label: 'Bigger role +3.4 min',
      tone: 'win',
      why: 'Projected 31.9 min vs 28.5 last season',
      signal: true,
      value: 3.4,
    },
    {
      code: 'certainty',
      label: 'Low certainty',
      tone: 'warn',
      why: 'Games and minutes are among the least predictable third of the pool',
      signal: false,
      value: 0.41,
    },
  ],
  203999: [
    {
      code: 'certainty',
      label: 'High certainty',
      tone: 'win',
      why: 'Games and minutes are among the most predictable third of the pool',
      signal: false,
      value: 0.08,
    },
    {
      code: 'consistency',
      label: 'Steady',
      tone: 'win',
      why: 'Weekly value varied ±0.9 last season (median ±1.3)',
      signal: false,
      value: null,
    },
    {
      code: 'age',
      label: 'Age 32',
      tone: 'neutral',
      why: '32 this season',
      signal: false,
      value: null,
    },
  ],
}
for (const p of samplePlayerRows) {
  p.indicators = sampleIndicators[p.id] ?? []
  p.signal = (p.indicators ?? []).find((i) => i.signal) ?? null
}

export const samplePlayers: Players = {
  variant: 'all',
  variants: ['all', 'punt_ast', 'punt_fg_pct', 'punt_tov'],
  players: samplePlayerRows,
  badgeNotes: [],
  freshness: {
    asOf: '2026-09-26T08:00:00Z',
    sources: [{ name: 'Draft projections', asOf: '2026-09-26T08:00:00Z' }],
  },
}

/** Reorders by a crude punt (drops the category's strength) so the demo's strategy picker visibly works. */
function samplePunt(variant: string): Players {
  const cat = variant.replace(/^punt_/, '')
  const score = (p: PlayerRow) => p.value - (p.strengths[cat] ?? 0)
  const players = [...samplePlayerRows]
    .sort((a, b) => score(b) - score(a))
    .map((p, i) => ({ ...p, rank: i + 1 }))
  return { ...samplePlayers, variant, players }
}

export const fixtureClient: ApiClient = {
  today: () => Promise.resolve(sampleToday),
  matchup: () => Promise.resolve(sampleMatchup),
  waivers: () => Promise.resolve(sampleWaivers),
  players: (variant) =>
    samplePlayers.variants.includes(variant)
      ? Promise.resolve(variant === 'all' ? samplePlayers : samplePunt(variant))
      : Promise.reject(new ApiError(422, '/problems/invalid-request', 'Unknown strategy')),
}
