import { fireEvent, render, screen, within } from '@testing-library/react'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players } from '../../api/types'
import { CATEGORIES } from '../players/format'
import { replayWithGames } from '../replay/fixtures/replayWithGames'
import values from './fixtures/values-2026-27.json'

const base = samplePlayers.players[0] as PlayerRow
const full: Players = {
  ...samplePlayers,
  players: values.players.map((v, i) => ({
    ...base,
    id: Number(v.id),
    name: `Player ${v.id}`,
    rank: i + 1,
    dollars: v.usd,
    badges: [],
    indicators: [],
    strengths: Object.fromEntries(CATEGORIES.map(([k], j) => [k, v.z[j] ?? 0])),
  })),
}
const client: ApiClient = { ...fixtureClient, players: () => Promise.resolve(full) }

async function finishDraft(season?: string) {
  fireEvent.click(await screen.findByRole('radio', { name: /Untimed/ }))
  if (season) {
    const select = screen.getByRole('combobox', { name: 'Season' })
    await within(select).findByRole('option', { name: `Replay ${season}` })
    fireEvent.change(select, { target: { value: season } })
  }
  fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Sim the rest' }))
  await screen.findByText('Your report')
}

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

describe('practice draft report (DRAFT-015 AC3)', () => {
  it('shows totals, nine category ranks, budget pace and the team', async () => {
    render(<App client={client} initialPath="/draft" />)
    await finishDraft()
    expect(screen.getByText('Surplus')).toBeInTheDocument()
    const ranks = screen.getByRole('list', { name: 'Category ranks' })
    expect(within(ranks).getAllByRole('listitem')).toHaveLength(9)
    expect(within(ranks).getAllByText(/of 16$/)).toHaveLength(9)
    expect(
      screen.getByRole('table', { name: /spending against the average rival/i }),
    ).toBeInTheDocument()
    expect(
      within(screen.getByRole('table', { name: 'Your drafted team' })).getAllByRole('row'),
    ).toHaveLength(15)
  }, 30_000)

  it('keeps a history of runs and can draft again', async () => {
    render(<App client={client} initialPath="/draft" />)
    await finishDraft()
    expect(screen.queryByRole('table', { name: /Past practice drafts/ })).toBeNull() // one run so far
    fireEvent.click(screen.getByRole('button', { name: 'Draft again' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Sim the rest' }))
    await screen.findByText('Your report')
    const past = screen.getByRole('table', { name: /Past practice drafts/ })
    expect(within(past).getAllByRole('row')).toHaveLength(3) // header + 2 runs
  }, 60_000)
})

describe('a past-season draft (SIM-002 AC2)', () => {
  const replayClient: ApiClient = {
    ...client,
    replaySeasons: () => Promise.resolve({ seasons: ['2024-25'] }),
    replaySeason: (s) => Promise.resolve(replayWithGames(s)),
  }

  it('play the season: saves the 16 rosters and opens the season replay', async () => {
    render(<App client={replayClient} initialPath="/draft" />)
    await finishDraft('2024-25')
    expect(screen.getByText('2024-25 replay draft complete')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Play the 2024-25 season' }))
    expect(
      await screen.findByRole('heading', { level: 1, name: /^Week 1 vs / }),
    ).toBeInTheDocument()
    const league = JSON.parse(localStorage.getItem('replay-league') ?? '{}') as {
      season: string
      rosters: Record<string, number[]>
    }
    expect(league.season).toBe('2024-25')
    expect(Object.keys(league.rosters)).toHaveLength(16)
    expect(Object.values(league.rosters).every((r) => r.length === 14)).toBe(true)
  }, 30_000)

  it('play the season asks before replacing a saved league', async () => {
    localStorage.setItem(
      'replay-league',
      JSON.stringify({
        version: 1,
        season: '2023-24',
        me: 'me',
        rosters: { me: [1] },
        savedAt: '2026-10-01T00:00:00Z',
        results: { '1': { opponent: 'Team 2', wins: 5, losses: 3, ties: 1 } },
      }),
    )
    render(<App client={replayClient} initialPath="/draft" />)
    await finishDraft('2024-25')
    fireEvent.click(screen.getByRole('button', { name: 'Play the 2024-25 season' }))
    const ask = screen.getByRole('group', { name: 'Replace the saved season' })
    expect(ask).toHaveTextContent('replaces your saved 2023-24 league and its 1 played weeks')
    fireEvent.click(within(ask).getByRole('button', { name: 'Keep the old one' }))
    expect(JSON.parse(localStorage.getItem('replay-league') ?? '{}').season).toBe('2023-24')
  }, 30_000)
})
