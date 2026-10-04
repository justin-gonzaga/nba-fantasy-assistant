import { tinyDoc } from './fixtures/tinySeason'
import { draftPool, parseSeason, weekDays, type ReplayWeek } from './season'

describe('season file (SIM-002)', () => {
  it('parses columnar lines by date and player', () => {
    const s = parseSeason(tinyDoc())
    expect(s.lines.get('2024-10-22')?.get(10)).toEqual({
      pts: 25,
      reb: 5,
      ast: 7,
      stl: 1,
      blk: 0,
      fg3m: 3,
      tov: 2,
      fgm: 9,
      fga: 18,
      ftm: 4,
      fta: 5,
    })
    expect(s.lines.get('2024-10-22')?.get(30)?.pts).toBe(4)
    expect(s.lines.get('2024-10-24')?.has(30)).toBe(false)
  })

  it('the draft pool is the valued players, best first', () => {
    expect(draftPool(parseSeason(tinyDoc())).map((p) => [p.id, p.usd])).toEqual([
      ['10', 40],
      ['20', 12.5],
    ])
  })

  it('weeks have every calendar day', () => {
    const s = parseSeason(tinyDoc())
    const [w1, w2] = s.weeks as [ReplayWeek, ReplayWeek]
    const days = weekDays(w1)
    expect(days).toEqual([
      '2024-10-22',
      '2024-10-23',
      '2024-10-24',
      '2024-10-25',
      '2024-10-26',
      '2024-10-27',
    ])
    expect(weekDays(w2)).toHaveLength(7)
  })
})
