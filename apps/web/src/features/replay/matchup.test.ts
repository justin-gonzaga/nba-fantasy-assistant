import {
  addPlayer,
  autoLineup,
  eligible,
  playWeek,
  type Line,
  type ReplayPlayer,
  type WeekState,
} from './matchup'

const z0 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
const player = (id: number, pos: string | null, usd: number): ReplayPlayer => ({
  id,
  name: `P${id}`,
  team: 'TST',
  pos,
  usd,
  rank: id,
  z: z0,
})
const line = (pts: number, extra: Partial<Line> = {}): Line => ({
  pts,
  reb: 0,
  ast: 0,
  stl: 0,
  blk: 0,
  fg3m: 0,
  tov: 0,
  fgm: 0,
  fga: 0,
  ftm: 0,
  fta: 0,
  ...extra,
})

describe('slots (SIM-003 AC1)', () => {
  it('positions fill their slots; G-F fills G or F; an unknown position is Util only', () => {
    expect(eligible('G-F', 'G')).toBe(true)
    expect(eligible('G-F', 'F')).toBe(true)
    expect(eligible('G-F', 'C')).toBe(false)
    expect(eligible('F-C', 'C')).toBe(true)
    expect(eligible(null, 'Util')).toBe(true)
    expect(eligible(null, 'G')).toBe(false)
  })

  it('the auto lineup starts the most valuable players with a game, using slots well', () => {
    // Greedy by value would put the G-F (most valuable) at G and strand the third G; matching doesn't.
    const players = new Map<number, ReplayPlayer>([
      [1, player(1, 'G-F', 50)],
      [2, player(2, 'G', 40)],
      [3, player(3, 'G', 30)],
      [4, player(4, 'G', 20)],
      [5, player(5, 'C', 10)],
      [6, player(6, 'C', 5)],
    ])
    const playing = new Set([1, 2, 3, 4, 5, 6])
    const lineup = autoLineup([1, 2, 3, 4, 5, 6], playing, players, new Set())
    expect(lineup.size).toBe(6) // everyone starts: 3 G + G-F at F + C + C at Util
    expect(lineup.has(4)).toBe(true)
    // nobody without a game starts; a benched player doesn't start
    const some = autoLineup([1, 2, 3], new Set([1, 2]), players, new Set([2]))
    expect([...some.keys()]).toEqual([1])
  })
})

// A two-day week: me (1, 2) vs them (3, 4); free agent 5.
const players = new Map<number, ReplayPlayer>([
  [1, player(1, 'G', 40)],
  [2, player(2, 'C', 30)],
  [3, player(3, 'G', 35)],
  [4, player(4, 'F', 25)],
  [5, player(5, 'F', 1)],
])
const days = ['2024-11-04', '2024-11-05']
const lines = new Map<string, Map<number, Line>>([
  [
    '2024-11-04',
    new Map([
      [1, line(20, { fgm: 8, fga: 16, tov: 3, reb: 4 })],
      [3, line(25, { fgm: 10, fga: 20, tov: 1 })],
    ]),
  ],
  [
    '2024-11-05',
    new Map([
      [2, line(10, { fgm: 4, fga: 5, reb: 12, tov: 2 })],
      [4, line(5, { fgm: 2, fga: 8, reb: 3 })],
      [5, line(30, { fgm: 12, fga: 18 })],
    ]),
  ],
])
const start = (): WeekState => ({
  days,
  mine: [1, 2],
  theirs: [3, 4],
  taken: new Set([1, 2, 3, 4]),
  moves: [],
  benched: new Map(),
})

describe('scoring (SIM-003 AC3)', () => {
  it('matches a hand-checked week', () => {
    const r = playWeek(start(), players, lines)
    const cat = (k: string) => r.categories.find((c) => c.key === k)
    // PTS 30 vs 30: tie
    expect(cat('pts')).toMatchObject({ mine: 30, theirs: 30, result: 'tie' })
    // REB 16 vs 3: win
    expect(cat('reb')).toMatchObject({ mine: 16, theirs: 3, result: 'win' })
    // FG% 12/21 = .571 vs 12/28 = .429: win
    expect(cat('fg_pct')?.result).toBe('win')
    expect(cat('fg_pct')?.mine).toBeCloseTo(12 / 21, 6)
    // TOV 5 vs 1: lower wins, so a loss
    expect(cat('tov')).toMatchObject({ mine: 5, theirs: 1, result: 'loss' })
    // FT% 0/0 vs 0/0: tie (no attempts)
    expect(cat('ft_pct')?.result).toBe('tie')
    expect(r.record).toEqual({ wins: 2, losses: 1, ties: 6 })
  })
})

describe('acquisitions (SIM-003 AC2)', () => {
  it('a pickup plays from the day after it is made, and the dropped player stops scoring', () => {
    // made on day 0 (Monday): plays from Tuesday, when player 5 scores 30
    const r = addPlayer(start(), 0, 5, 2)
    expect(r.error).toBeNull()
    const week = playWeek(r.state, players, lines)
    // Monday: 1 scores 20; Tuesday: 2 dropped (his 10 doesn't count), 5 scores 30 → 50
    expect(week.categories.find((c) => c.key === 'pts')?.mine).toBe(50)
  })

  it('made before the week (day −1), a pickup plays from Monday', () => {
    const r = addPlayer(start(), -1, 5, 1)
    expect(playWeek(r.state, players, lines).categories.find((c) => c.key === 'pts')?.mine).toBe(40)
  })

  it('allows four adds a week and refuses a fifth, a taken player and a drop you do not own', () => {
    const many = new Map(players)
    for (let i = 6; i <= 11; i++) many.set(i, player(i, 'G', 1))
    let s: WeekState = {
      ...start(),
      mine: [1, 2, 6, 7, 8, 9],
      taken: new Set([1, 2, 3, 4, 6, 7, 8, 9]),
    }
    for (const [add, drop] of [
      [5, 6],
      [10, 7],
      [11, 8],
    ] as const) {
      const r = addPlayer(s, -1, add, drop)
      expect(r.error).toBeNull()
      s = r.state
    }
    expect(addPlayer(s, -1, 3, 9).error).toMatch(/not a free agent/)
    expect(addPlayer(s, -1, 6, 4).error).toMatch(/not on your roster/)
    const fourth = addPlayer(s, -1, 6, 9) // 6 was dropped: a free agent again
    expect(fourth.error).toBeNull()
    expect(addPlayer(fourth.state, -1, 7, 1).error).toMatch(/4 adds/)
  })
})
