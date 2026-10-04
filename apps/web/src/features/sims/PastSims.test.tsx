import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players, SimIn } from '../../api/types'
import values from '../draft/fixtures/values-2026-27.json'
import { CATEGORIES } from '../players/format'
import { draftedLeague, replayWithGames } from '../replay/fixtures/replayWithGames'
import { leagueSim } from './sync'
import { fakeSims } from './fakeSims'

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

const run = (i: number, title: string, surplus: number, wins: number): SimIn => ({
  id: `run:${i}`,
  kind: 'practice',
  season: '2026-27',
  title,
  summary: { surplus, categoryWins: wins, counted: 9, at: `2026-10-0${i}` },
  detail: {},
})

async function setup(seed: SimIn[] = []) {
  const fake = fakeSims()
  for (const s of seed) await fake.api.save(s)
  const client: ApiClient = {
    ...fixtureClient,
    players: () => Promise.resolve(full),
    replaySeasons: () => Promise.resolve({ seasons: ['2024-25'] }),
    replaySeason: (s) => Promise.resolve(replayWithGames(s)),
    sims: fake.api,
  }
  return { fake, client }
}

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

describe('past sims (SIM-006)', () => {
  it('list: practice drafts and season replays, with a trend', async () => {
    const { client } = await setup([
      run(1, 'All categories', -4, 4.1),
      run(2, 'Punt FT%', 9, 5.2),
      run(3, 'All categories', 3, 4.8),
      leagueSim(draftedLeague()),
    ])
    render(<App client={client} initialPath="/sims" />)
    const list = await screen.findByRole('list', { name: 'Your practice drafts' })
    expect(within(list).getAllByRole('listitem')).toHaveLength(3)
    expect(screen.getByRole('button', { name: 'Season replays (1)' })).toBeInTheDocument()
    expect(
      screen.getByRole('img', {
        name: /Surplus over your last 3 runs: from −\$4 to \+\$3, best \+\$9/,
      }),
    ).toBeInTheDocument()
  })

  it('sort and filter', async () => {
    const { client } = await setup([
      run(1, 'All categories', -4, 4.1),
      run(2, 'Punt FT%', 9, 5.2),
      run(3, 'All categories', 3, 4.8),
    ])
    render(<App client={client} initialPath="/sims" />)
    const list = await screen.findByRole('list', { name: 'Your practice drafts' })
    expect(within(list).getAllByRole('listitem')[0]).toHaveTextContent('2026-10-03')
    fireEvent.change(screen.getByRole('combobox', { name: 'Sort' }), {
      target: { value: 'surplus' },
    })
    expect(within(list).getAllByRole('listitem')[0]).toHaveTextContent('Punt FT%')
    fireEvent.change(screen.getByRole('combobox', { name: 'Strategy' }), {
      target: { value: 'All categories' },
    })
    expect(within(list).getAllByRole('listitem')).toHaveLength(2)
  })

  it('empty', async () => {
    const { client } = await setup()
    render(<App client={client} initialPath="/sims" />)
    expect(await screen.findByText('No practice drafts yet')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Season replays (0)' }))
    expect(screen.getByText('No season replays yet')).toBeInTheDocument()
  })

  it('reopen: a finished practice draft is kept with the account and its full report reopens', async () => {
    const { client, fake } = await setup()
    render(<App client={client} initialPath="/draft" />)
    fireEvent.click(await screen.findByRole('radio', { name: /Untimed/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Sim the rest' }))
    await screen.findByText('Your report')
    await waitFor(() => expect(fake.sims.size).toBe(1))
    const [saved] = [...fake.sims.values()]
    expect(saved?.kind).toBe('practice')
    render(<App client={client} initialPath="/sims" />)
    const list = await screen.findAllByRole('list', { name: 'Your practice drafts' })
    fireEvent.click(within(list[0] as HTMLElement).getByRole('link', { name: 'Open' }))
    const ranks = await screen.findByRole('list', { name: 'Category ranks' })
    expect(within(ranks).getAllByRole('listitem')).toHaveLength(9)
    expect(screen.getByRole('table', { name: 'Your drafted team' })).toBeInTheDocument()
  }, 30_000)

  it('reopen: a trimmed run says only its summary is kept', async () => {
    const { client } = await setup([run(1, 'All categories', 6, 4.5)])
    render(<App client={client} initialPath="/sims/run%3A1" />)
    expect(await screen.findByText(/Only the summary is kept for this run/)).toBeInTheDocument()
    expect(screen.getByText(/Surplus \+\$6/)).toBeInTheDocument()
  })

  it('pin: up to 10, then why', async () => {
    const seed = Array.from({ length: 11 }, (_, i) => run(i + 1, `Run ${i + 1}`, i, 4))
    const { client } = await setup(seed)
    render(<App client={client} initialPath="/sims" />)
    await screen.findByRole('list', { name: 'Your practice drafts' })
    for (let i = 1; i <= 10; i++) {
      fireEvent.click(screen.getByRole('button', { name: new RegExp(`^Pin Run ${i},`) }))
      await screen.findByRole('button', { name: new RegExp(`^Unpin Run ${i},`) })
    }
    fireEvent.click(screen.getByRole('button', { name: /^Pin Run 11,/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('You can pin 10 runs')
  })

  it('delete asks in the page first', async () => {
    const { client, fake } = await setup([run(1, 'All categories', 6, 4.5)])
    render(<App client={client} initialPath="/sims" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Delete…' }))
    const ask = screen.getByRole('group', { name: 'Delete this run?' })
    fireEvent.click(within(ask).getByRole('button', { name: 'Keep' }))
    expect(fake.sims.size).toBe(1)
    fireEvent.click(screen.getByRole('button', { name: 'Delete…' }))
    fireEvent.click(
      within(screen.getByRole('group', { name: 'Delete this run?' })).getByRole('button', {
        name: 'Delete',
      }),
    )
    expect(await screen.findByText('No practice drafts yet')).toBeInTheDocument()
    expect(fake.sims.size).toBe(0)
  })

  it('continue a season replay on this device', async () => {
    const league = draftedLeague()
    const { client } = await setup([leagueSim(league)])
    render(<App client={client} initialPath="/sims" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Season replays (1)' }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Week 1 vs Team 2' }),
    ).toBeInTheDocument()
    expect(JSON.parse(localStorage.getItem('replay-league') ?? '{}').season).toBe('2024-25')
  })

  it('signed out (no account), it says sims need sign-in', async () => {
    render(<App client={{ ...fixtureClient }} initialPath="/sims" />)
    expect(await screen.findByText(/Sign in to keep your practice drafts/)).toBeInTheDocument()
  })
})
