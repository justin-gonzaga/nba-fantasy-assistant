import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players } from '../../api/types'

/** A window `width` px wide: every `(min-width: N px)` query up to it matches. */
function viewport(width: number) {
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (q: string) =>
      ({
        matches: Number(/min-width:\s*(\d+)px/.exec(q)?.[1] ?? Infinity) <= width,
        media: q,
        addEventListener: () => {},
        removeEventListener: () => {},
      }) as unknown as MediaQueryList,
  )
}

const base = samplePlayers.players[0] as PlayerRow
const data: Players = {
  ...samplePlayers,
  players: Array.from({ length: 60 }, (_, i) => ({
    ...base,
    id: 3000 + i,
    rank: i + 1,
    name: `Player ${i + 1}`,
    dollars: 70 - i,
    badges: i === 4 ? (samplePlayers.players[6] as PlayerRow).badges : [],
    strengths: { ...base.strengths, pts: i % 7 }, // Player 7 has the best PTS impact
  })),
}
const client: ApiClient = { ...fixtureClient, players: () => Promise.resolve(data) }

const table = () => screen.getByRole('table', { name: 'Players' })
const bodyRows = () => within(table()).getAllByRole('row').slice(1)
const firstName = () => within(bodyRows()[0] as HTMLElement).getByRole('button').textContent

afterEach(() => vi.restoreAllMocks())

describe('Players desktop table (WEB-024 AC1)', () => {
  it('shows a table with the stat line columns at 1280 px', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    const headers = within(table())
      .getAllByRole('columnheader')
      .map((h) => h.textContent?.replace(/[▲▼]/g, ''))
    expect(headers).toEqual([
      '#',
      'Player',
      '$',
      'PTS',
      'REB',
      'AST',
      'STL',
      'BLK',
      '3PM',
      'FG%',
      'FT%',
      'TO',
    ])
    expect(bodyRows()).toHaveLength(50) // paging kept
    const dollars = within(bodyRows()[0] as HTMLElement).getAllByRole('cell')[2] as HTMLElement
    expect(dollars).toHaveClass('text-right', 'tabular-nums')
    expect(screen.queryByRole('list', { name: 'Players' })).toBeNull()
  })

  it('sorts by a header, flips on a second click, and marks aria-sort', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    const rankTh = screen.getByRole('columnheader', { name: '#' })
    expect(rankTh).toHaveAttribute('aria-sort', 'ascending')
    await userEvent.click(screen.getByRole('button', { name: 'PTS' }))
    const pts = screen.getByRole('columnheader', { name: 'PTS' })
    expect(pts).toHaveAttribute('aria-sort', 'descending')
    expect(rankTh).not.toHaveAttribute('aria-sort')
    expect(firstName()).toBe('Player 7')
    await userEvent.click(screen.getByRole('button', { name: 'PTS' }))
    expect(pts).toHaveAttribute('aria-sort', 'ascending')
    expect(firstName()).toBe('Player 1') // lowest impact, rank breaks the tie
  })
})

describe('Players sort direction in the URL (WEB-024 AC1)', () => {
  it('reads ?sort=pts&dir=asc on first load', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players?sort=pts&dir=asc" />)
    await screen.findByRole('table', { name: 'Players' })
    expect(screen.getByRole('columnheader', { name: 'PTS' })).toHaveAttribute(
      'aria-sort',
      'ascending',
    )
    expect(firstName()).toBe('Player 1')
  })
})

describe('Players desktop toolbar (WEB-024 AC2)', () => {
  it('puts badge and signal filters in a Filters popover with counts; active ones are removable', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    expect(screen.queryByRole('group', { name: 'Filter by badge' })).toBeNull()
    const filters = screen.getByRole('button', { name: 'Filters' })
    expect(filters).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(filters)
    const pop = within(screen.getByRole('group', { name: 'Filter by badge' }))
    const chip = pop.getByRole('button', { name: /^Injury prone 1$/ })
    expect(pop.queryByRole('button', { name: /^Breakout/ })).toBeNull() // zero matches: hidden
    await userEvent.click(chip)
    expect(bodyRows()).toHaveLength(1)
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('group', { name: 'Filter by badge' })).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: 'Remove filter: Injury prone' }))
    expect(bodyRows()).toHaveLength(50)
  })
})

describe('Players detail panel (WEB-024 AC3)', () => {
  it('opens a right panel at 1280 px; the table stays, Escape closes and focus returns', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    const trigger = within(bodyRows()[2] as HTMLElement).getByRole('button')
    await userEvent.click(trigger)
    expect(screen.queryByRole('dialog')).toBeNull()
    const panel = screen.getByRole('complementary', { name: 'Player 3' })
    expect(within(panel).getByRole('heading', { name: 'Player 3' })).toBeInTheDocument()
    expect(bodyRows()[2]).toHaveAttribute('data-selected', 'true')
    // Beside the panel below 1600 px the table keeps #, Player and $; the panel has the line.
    expect(within(table()).getAllByRole('columnheader')).toHaveLength(3)
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('complementary', { name: 'Player 3' })).toBeNull()
    expect(trigger).toHaveFocus()
  })

  it('Escape with the Filters popover open closes only the popover', async () => {
    viewport(1280)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    await userEvent.click(within(bodyRows()[0] as HTMLElement).getByRole('button'))
    await userEvent.click(screen.getByRole('button', { name: 'Filters' }))
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('group', { name: 'Filter by badge' })).toBeNull()
    expect(screen.getByRole('complementary', { name: 'Player 1' })).toBeInTheDocument()
  })

  it('keeps the sheet between 840 and 1199 px', async () => {
    viewport(1000)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    await userEvent.click(within(bodyRows()[0] as HTMLElement).getByRole('button'))
    expect(screen.getByRole('dialog', { name: 'Player 1' })).toBeInTheDocument()
  })
})

describe('Players on phones (WEB-024 AC4)', () => {
  it('keeps the card list and the chip filters', async () => {
    viewport(390)
    render(<App client={client} initialPath="/players" />)
    await screen.findByRole('list', { name: 'Players' })
    expect(screen.queryByRole('table', { name: 'Players' })).toBeNull()
    expect(screen.getByRole('group', { name: 'Filter by badge' })).toBeInTheDocument()
  })
})

describe('low-minute players (WEB-027)', () => {
  const small: Players = {
    ...samplePlayers,
    players: Array.from({ length: 30 }, (_, i) => ({
      ...base,
      id: 4000 + i,
      rank: i + 1,
      name: `Player ${i + 1}`,
      badges: [],
      strengths: { ...base.strengths, tov: i === 29 ? 5 : i / 10 },
      projection:
        i === 29
          ? { ...(base.projection as NonNullable<PlayerRow['projection']>), mpg: 8 }
          : base.projection,
    })),
  }
  const smallClient: ApiClient = { ...fixtureClient, players: () => Promise.resolve(small) }

  it('sorts them after everyone in category columns, both ways, and mutes their figures', async () => {
    viewport(1280)
    render(<App client={smallClient} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    await userEvent.click(screen.getByRole('button', { name: 'TO' }))
    expect(firstName()).toBe('Player 29') // best TO among rotation players
    expect(within(bodyRows()[29] as HTMLElement).getByRole('button').textContent).toBe('Player 30')
    await userEvent.click(screen.getByRole('button', { name: 'TO' }))
    expect(firstName()).toBe('Player 1')
    expect(within(bodyRows()[29] as HTMLElement).getByRole('button').textContent).toBe('Player 30')
    const cells = within(bodyRows()[29] as HTMLElement).getAllByRole('cell')
    expect(cells[cells.length - 1]).toHaveAttribute('title', 'Under 20 min/game projected')
    expect(cells[cells.length - 1]).toHaveClass('text-muted')
  })

  it('leaves rank order alone', async () => {
    viewport(1280)
    render(<App client={smallClient} initialPath="/players" />)
    await screen.findByRole('table', { name: 'Players' })
    expect(within(bodyRows()[29] as HTMLElement).getByRole('button').textContent).toBe('Player 30')
    expect(firstName()).toBe('Player 1')
  })
})
