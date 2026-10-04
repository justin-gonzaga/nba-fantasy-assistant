import { playWeek, type Line, type ReplayPlayer, type WeekState } from './matchup'
import {
  averagesBefore,
  gamesInWeek,
  hasGame,
  projectedLines,
  teamGamesInWeek,
  teamNames,
  teamOn,
} from './schedule'
import { parseSeason, weekDays, type ReplayDoc } from './season'

const z = [0, 0, 0, 0, 0, 0, 0, 0, 0]
const P = (id: number, team: string, pos: string, usd: number): ReplayPlayer => ({
  id,
  name: `P${id}`,
  team,
  pos,
  usd,
  rank: id,
  z,
})

// Week 2024-10-28 (Mon) … 11-03. Team 1 = BOS, 2 = LAL, 3 = NYK.
// 10 (BOS) plays Tue, sits out Thu (BOS plays: 99's line). 30 is traded BOS → NYK, first NYK game Thu.
const rows: [string, number, number, number][] = [
  // date, player, team, pts
  ['2024-10-22', 10, 1, 20],
  ['2024-10-22', 30, 1, 8],
  ['2024-10-29', 10, 1, 30],
  ['2024-10-30', 20, 2, 12],
  ['2024-10-31', 30, 3, 15],
  ['2024-10-31', 99, 1, 9],
  ['2024-11-01', 20, 2, 14],
]
const dates = [...new Set(rows.map((r) => r[0]))]
const col = (f: (r: (typeof rows)[number]) => number) => rows.map(f)
const zeros = rows.map(() => 0)
const doc: ReplayDoc = {
  season: '2024-25',
  method: 'ours',
  players: [
    P(10, 'BOS', 'G', 40),
    P(20, 'LAL', 'C', 30),
    P(30, 'BOS', 'F', 5),
    P(99, 'BOS', 'G', 1),
  ],
  weeks: [{ week: 2, start: '2024-10-28', end: '2024-11-03' }],
  lines: {
    dates,
    players: col((r) => r[1]),
    day: col((r) => dates.indexOf(r[0])),
    team: col((r) => r[2]),
    min: zeros,
    pts: col((r) => r[3]),
    reb: zeros,
    ast: zeros,
    stl: zeros,
    blk: zeros,
    fg3m: zeros,
    tov: zeros,
    fgm: zeros,
    fga: zeros,
    ftm: zeros,
    fta: zeros,
  },
}
const s = parseSeason(doc)
const days = weekDays({ week: 2, start: '2024-10-28', end: '2024-11-03' })

describe('schedule (SIM-004 AC4)', () => {
  it('a player who sat out still has a game: the schedule is the team’s', () => {
    expect(hasGame(s, 10, '2024-10-29')).toBe(true) // played
    expect(hasGame(s, 10, '2024-10-31')).toBe(true) // BOS played; he didn't (DNP)
    expect(hasGame(s, 10, '2024-10-30')).toBe(false)
    expect(gamesInWeek(s, 10, days)).toBe(2)
    expect(gamesInWeek(s, 20, days)).toBe(2)
  })

  it('a traded player follows his latest team; his game days for the new team count', () => {
    expect(teamOn(s, 30, '2024-10-31')).toBe(1) // before his first NYK game: last seen with BOS
    expect(teamOn(s, 30, '2024-11-02')).toBe(3)
    expect(hasGame(s, 30, '2024-10-31')).toBe(true) // his first NYK game (he has a line)
    expect(gamesInWeek(s, 30, days)).toBe(2) // BOS Tue (assumed) + NYK Thu
  })

  it('counts games per NBA team and names the teams', () => {
    const t = teamGamesInWeek(s, days)
    expect([t.get(1), t.get(2), t.get(3)]).toEqual([2, 2, 1])
    expect(teamNames(s).get(1)).toBe('BOS')
    expect(teamNames(s).get(2)).toBe('LAL')
  })

  it('projections use only games before the week', () => {
    expect(averagesBefore(s, 10, '2024-10-28')?.pts).toBe(20) // the 10-22 game only
    expect(averagesBefore(s, 20, '2024-10-28')).toBeNull()
    const proj = projectedLines(s, [10, 20], days)
    expect(proj.get('2024-10-29')?.get(10)?.pts).toBe(20)
    expect(proj.get('2024-10-31')?.get(10)?.pts).toBe(20) // a scheduled game, whatever happened
    expect(proj.get('2024-10-30')?.has(20)).toBe(false) // no history yet
  })
})

describe('the engine by schedule (SIM-004 AC4)', () => {
  it('a scheduled player who sat out still takes the slot', () => {
    // Thursday: seven guards with games; the best (10) sits out. Six G/Util slots: the 7th guard is benched,
    // as in Yahoo where the lineup is set before tip-off.
    const guards = [10, 101, 102, 103, 104, 105, 99]
    const players = new Map<number, ReplayPlayer>(
      guards.map((id, i) => [id, P(id, 'BOS', 'G', 100 - i * 10)]),
    )
    const thu = '2024-10-31'
    const line = (pts: number): Line => ({
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
    })
    const lines = new Map([
      [thu, new Map(guards.filter((g) => g !== 10).map((g) => [g, line(10)]))],
    ])
    const state: WeekState = {
      days: [thu],
      mine: guards,
      theirs: [],
      taken: new Set(guards),
      moves: [],
      benched: new Map(),
    }
    const scheduled = () => true
    const bySchedule = playWeek(state, players, lines, scheduled)
    expect(bySchedule.days[0]?.mine).toContain(10)
    expect(bySchedule.days[0]?.mine).not.toContain(99)
    expect(bySchedule.categories.find((c) => c.key === 'pts')?.mine).toBe(50)
    const byLines = playWeek(state, players, lines) // hindsight: knows 10 sat out
    expect(byLines.categories.find((c) => c.key === 'pts')?.mine).toBe(60)
  })
})
