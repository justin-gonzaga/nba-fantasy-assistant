import { tinyDoc } from './fixtures/tinySeason'
import type { ReplayLeague } from './league'
import { addPlayer, playWeek } from './matchup'
import { parseSeason, type ReplayWeek } from './season'
import { defaultRival, freeAgents, keepWeek, nextWeek, seasonRecord, startWeek } from './week'

const league = (): ReplayLeague => ({
  version: 1,
  season: '2024-25',
  me: 'me',
  rosters: { me: [10], 'Team 2': [20], 'Team 3': [] },
  savedAt: '2026-10-04T00:00:00Z',
  results: {},
})

describe('a replay week (SIM-004)', () => {
  const s = parseSeason(tinyDoc())
  const [w1, w2] = s.weeks as [ReplayWeek, ReplayWeek]

  it('rivals rotate by week; the next week is the first unplayed', () => {
    expect(defaultRival(league(), 1)).toBe('Team 2')
    expect(defaultRival(league(), 2)).toBe('Team 3')
    expect(defaultRival(league(), 3)).toBe('Team 2')
    expect(nextWeek(league(), s.weeks)?.week).toBe(1)
    const played = {
      ...league(),
      results: { '1': { opponent: 'Team 2', wins: 5, losses: 4, ties: 0 } },
    }
    expect(nextWeek(played, s.weeks)?.week).toBe(2)
  })

  it('free agents are the unrostered players with games this week, most games first', () => {
    const st = startWeek(league(), w1, 'Team 2')
    expect(freeAgents(s, st).map((f) => [f.player.id, f.games])).toEqual([[30, 1]])
    // dropping 10 for 30 makes 10 a free agent again
    const moved = addPlayer(st, -1, 30, 10).state
    expect(freeAgents(s, moved).map((f) => f.player.id)).toEqual([10])
    // …and picking him back up (dropping 30) makes 30 the free agent, not 10
    const back = addPlayer(moved, -1, 10, 30).state
    expect(freeAgents(s, back).map((f) => f.player.id)).toEqual([30])
  })

  it('keeping a week records it and carries the pickups into the roster', () => {
    const st = addPlayer(startWeek(league(), w1, 'Team 2'), -1, 30, 10).state
    const result = playWeek(st, s.players, s.lines)
    const kept = keepWeek(league(), 1, 'Team 2', st, result)
    expect(kept.rosters.me).toEqual([30])
    expect(kept.results['1']?.opponent).toBe('Team 2')
    expect(seasonRecord(kept).wins + seasonRecord(kept).losses + seasonRecord(kept).ties).toBe(1)
    expect(startWeek(kept, w2, 'Team 3').mine).toEqual([30])
  })
})
