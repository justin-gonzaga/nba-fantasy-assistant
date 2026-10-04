import { leagueFromSales, loadLeague, saveLeague } from './league'

const memory = () => {
  const m = new Map<string, string>()
  return {
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
  }
}

describe('replay league (SIM-002)', () => {
  it('collects each team’s roster from the sales and round-trips through storage', () => {
    const league = leagueFromSales(
      '2024-25',
      ['me', 'Team 2', 'Team 3'],
      'me',
      [
        { pid: '10', team: 'me', price: 40 },
        { pid: '20', team: 'Team 2', price: 12 },
        { pid: '30', team: 'me', price: 1 },
      ],
      '2026-10-04T10:00:00Z',
    )
    expect(league.rosters).toEqual({ me: [10, 30], 'Team 2': [20], 'Team 3': [] })
    const s = memory()
    saveLeague(league, s)
    expect(loadLeague(s)).toEqual(league)
  })

  it('a missing, corrupt or old-shaped entry loads as none', () => {
    const s = memory()
    expect(loadLeague(s)).toBeNull()
    s.setItem('replay-league', '{not json')
    expect(loadLeague(s)).toBeNull()
    s.setItem('replay-league', JSON.stringify({ season: '2024-25' }))
    expect(loadLeague(s)).toBeNull()
    const blocked = {
      getItem: () => {
        throw new Error('blocked')
      },
    }
    expect(loadLeague(blocked)).toBeNull()
  })
})
