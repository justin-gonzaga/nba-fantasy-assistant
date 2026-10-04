import { fireEvent, render, screen, within } from '@testing-library/react'
import { App } from '../../App'
import { fixtureClient } from '../../api/fixtures'
import type { ApiClient } from '../../api/types'
import { draftedLeague, replayWithGames } from './fixtures/replayWithGames'
import { saveLeague } from './league'

const client: ApiClient = {
  ...fixtureClient,
  replaySeasons: () => Promise.resolve({ seasons: ['2024-25'] }),
  replaySeason: (s) => Promise.resolve(replayWithGames(s)),
}

beforeEach(() => {
  localStorage.clear()
  saveLeague(draftedLeague())
})
afterEach(() => localStorage.clear())

const open = async () => {
  render(<App client={client} initialPath="/replay" />)
  return screen.findByRole('heading', { level: 1, name: 'Week 1 vs Team 2' })
}

describe('matchup simulator (SIM-004)', () => {
  it('choose week and rival: both schedules, games and the waiver pool render', async () => {
    await open()
    const mine = screen.getByRole('table', { name: 'Your team’s week' })
    expect(within(mine).getAllByRole('row')).toHaveLength(1 + 14 + 1) // head, 14 players, starts
    expect(within(mine).getAllByRole('columnheader')).toHaveLength(2 + 6) // week 1 is Tue-Sun
    fireEvent.change(screen.getByRole('combobox', { name: 'Week' }), { target: { value: '2' } })
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Week 2 vs Team 3' }),
    ).toBeInTheDocument()
    fireEvent.change(screen.getByRole('combobox', { name: 'Rival' }), {
      target: { value: 'Team 9' },
    })
    expect(screen.getByRole('heading', { level: 1, name: 'Week 2 vs Team 9' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Team 9’s week' })).toBeInTheDocument()
    const pool = within(screen.getByRole('list', { name: 'Free agents' })).getAllByRole('listitem')
    expect(pool.length).toBeGreaterThan(0)
    expect(pool[0]).toHaveTextContent(/\d games?/)
    expect(screen.getByText(/Games by NBA team this week:/)).toBeInTheDocument()
  })

  it('a player who sat out still shows his scheduled game (no hindsight)', async () => {
    await open()
    // Every 7th valued player sits out his team's second game; the grid still shows a game that day.
    const mine = screen.getByRole('table', { name: 'Your team’s week' })
    expect(within(mine).queryAllByLabelText(/: no game$/).length).toBeGreaterThan(0)
    expect(
      within(mine).queryAllByRole('button', { name: /starts\. Bench him$/ }).length,
    ).toBeGreaterThan(0)
  })

  it('pickups: four a week, add + drop, then adds are off with why', async () => {
    await open()
    for (let n = 0; n < 4; n++) {
      const add = within(screen.getByRole('list', { name: 'Free agents' })).getAllByRole('button', {
        name: /^Add /,
      })[0]
      if (!add) throw new Error('no free agent')
      fireEvent.click(add)
      const group = screen.getByRole('group', { name: /^Pick up / })
      fireEvent.click(within(group).getByRole('button', { name: 'Confirm' }))
      expect(screen.getByText(`${3 - n} of 4`)).toBeInTheDocument()
    }
    expect(
      within(screen.getByRole('list', { name: 'Your pickups this week' })).getAllByRole('listitem'),
    ).toHaveLength(4)
    for (const b of within(screen.getByRole('list', { name: 'Free agents' })).getAllByRole(
      'button',
      { name: /^Add / },
    ))
      expect(b).toBeDisabled()
    expect(screen.getByText(/used all 4 adds this week/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Undo' }))
    expect(screen.getByText('1 of 4')).toBeInTheDocument()
  })

  it('lineup: benching a starter for a day, and starting him again', async () => {
    await open()
    const mine = screen.getByRole('table', { name: 'Your team’s week' })
    const cell = within(mine).getAllByRole('button', { name: /starts\. Bench him$/ })[0]
    if (!cell) throw new Error('no starter')
    const who = (cell.getAttribute('aria-label') ?? '').split(':')[0] ?? ''
    fireEvent.click(cell)
    const off = within(mine).getAllByRole('button', { name: /benched by you\. Start him$/ })[0]
    expect(off).toHaveAttribute('aria-pressed', 'true')
    expect(off?.getAttribute('aria-label')).toContain(who)
    fireEvent.click(off as HTMLElement)
    expect(within(mine).queryAllByRole('button', { name: /benched by you/ })).toHaveLength(0)
  })

  it('play the week: result, categories, day by day; keeping it updates the season', async () => {
    await open()
    fireEvent.click(screen.getByRole('button', { name: 'Play the week' }))
    expect(screen.getByText(/^(Won|Lost|Tied) \d-\d-\d$/)).toBeInTheDocument()
    expect(
      within(screen.getByRole('table', { name: 'Category results' })).getAllByRole('row'),
    ).toHaveLength(10)
    expect(
      within(screen.getByRole('list', { name: 'Day by day' })).getAllByRole('listitem'),
    ).toHaveLength(6)
    fireEvent.click(screen.getByRole('button', { name: 'Keep this result' }))
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Week 1 vs Team 2' }),
    ).toBeInTheDocument()
    expect(screen.getByText(/You kept/)).toBeInTheDocument()
    const saved = JSON.parse(localStorage.getItem('replay-league') ?? '{}') as {
      results: Record<string, { opponent: string }>
    }
    expect(saved.results['1']?.opponent).toBe('Team 2')
    expect(screen.getByText(/^[01]-[01]-[01]$/)).toBeInTheDocument() // the season record
  })

  it('projections: none before any games are played, then from earlier games only', async () => {
    await open()
    expect(screen.getByText(/nothing to project from yet/)).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: 'Projected categories' })).toBeNull()
    fireEvent.change(screen.getByRole('combobox', { name: 'Week' }), { target: { value: '2' } })
    const table = await screen.findByRole('table', { name: 'Projected categories' })
    expect(within(table).getAllByRole('row')).toHaveLength(10)
    expect(screen.getByText(/Projected \d-\d-\d\./)).toBeInTheDocument()
  })

  it('without a saved league it points to draft practice', async () => {
    localStorage.clear()
    render(<App client={client} initialPath="/replay" />)
    expect(await screen.findByText('No replay league yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Draft practice' })).toHaveAttribute('href', '/draft')
  })
})
