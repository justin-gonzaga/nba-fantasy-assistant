import { samplePlayers } from '../../api/fixtures'
import type { PlayerRow } from '../../api/types'
import { MIN_POOL, categoryPercentiles } from './percentiles'

const base = samplePlayers.players[0] as PlayerRow
const pool = (n: number, over: (i: number) => Partial<PlayerRow> = () => ({})) =>
  Array.from({ length: n }, (_, i) => ({
    ...base,
    id: i,
    inPool: true,
    strengths: { ...base.strengths, pts: i, tov: -i },
    ...over(i),
  }))

describe('categoryPercentiles (WEB-025 AC1)', () => {
  it('ranks against in-pool players: share at or below, 0-100', () => {
    const players = pool(40)
    const top = categoryPercentiles(players[39] as PlayerRow, players)
    const bottom = categoryPercentiles(players[0] as PlayerRow, players)
    expect(top?.find((c) => c.key === 'pts')?.percentile).toBe(100)
    expect(bottom?.find((c) => c.key === 'pts')?.percentile).toBe(3) // 1 of 40
  })

  it('TOV strengths are signed so a higher percentile means fewer turnovers', () => {
    const players = pool(40) // tov strength −i: player 0 turns it over least
    const careful = categoryPercentiles(players[0] as PlayerRow, players)
    expect(careful?.find((c) => c.key === 'tov')?.percentile).toBe(100)
  })

  it('ignores players outside the expected draft pool', () => {
    const players = pool(60, (i) => ({ inPool: i >= 20 })) // pool = players 20..59
    const p = categoryPercentiles(players[20] as PlayerRow, players)
    expect(p?.find((c) => c.key === 'pts')?.percentile).toBe(3) // lowest of 40, not 21st of 60
  })

  it('ties share the percentile of the group (share at or below)', () => {
    const players = pool(40, (i) => ({ strengths: { ...base.strengths, pts: i < 20 ? 0 : 1 } }))
    const low = categoryPercentiles(players[0] as PlayerRow, players)
    const high = categoryPercentiles(players[39] as PlayerRow, players)
    expect(low?.find((c) => c.key === 'pts')?.percentile).toBe(50)
    expect(high?.find((c) => c.key === 'pts')?.percentile).toBe(100)
  })

  it('leaves players under 20 projected minutes out of the pool (WEB-027)', () => {
    const players = pool(50, (i) =>
      i < 10
        ? { projection: { ...(base.projection as NonNullable<PlayerRow['projection']>), mpg: 8 } }
        : {},
    )
    const p = categoryPercentiles(players[10] as PlayerRow, players)
    expect(p?.find((c) => c.key === 'pts')?.percentile).toBe(3) // lowest of the 40 rotation players
  })

  it(`returns null under ${MIN_POOL} pool players`, () => {
    const players = pool(MIN_POOL - 1)
    expect(categoryPercentiles(players[0] as PlayerRow, players)).toBeNull()
  })

  it('covers all nine categories in the category order', () => {
    const players = pool(MIN_POOL)
    expect(categoryPercentiles(players[0] as PlayerRow, players)?.map((c) => c.label)).toEqual([
      'PTS',
      'REB',
      'AST',
      'STL',
      'BLK',
      '3PM',
      'FG%',
      'FT%',
      'TOV',
    ])
  })
})
