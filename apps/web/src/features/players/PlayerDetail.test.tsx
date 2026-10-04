import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players } from '../../api/types'

const base = samplePlayers.players[0] as PlayerRow

const big: Players = {
  ...samplePlayers,
  players: Array.from({ length: 40 }, (_, i) => ({
    ...base,
    id: 2000 + i,
    rank: i + 1,
    name: `Player ${i + 1}`,
    inPool: true,
    strengths: { ...base.strengths, pts: 40 - i },
  })),
}

const client = (data: Players): ApiClient => ({
  ...fixtureClient,
  players: () => Promise.resolve(data),
})

async function open(data?: Players, index = 0) {
  render(<App {...(data ? { client: client(data) } : {})} initialPath="/players" />)
  const items = await screen.findAllByRole('listitem')
  await userEvent.click(within(items[index] as HTMLElement).getByRole('button'))
  return within(screen.getByRole('dialog'))
}

describe('Player detail anatomy (WEB-025)', () => {
  it('AC2: sections follow §9 order with a key figures strip first', async () => {
    const d = await open()
    expect(d.getAllByRole('heading', { level: 3 }).map((h) => h.textContent)).toEqual([
      'Category profile',
      'Projected per game',
      'At a glance',
      'Badges',
    ])
    const figures = within(d.getByRole('list', { name: 'Key figures' }))
    expect(figures.getByText('Value')).toBeInTheDocument()
    expect(figures.getByText('Rank')).toBeInTheDocument()
    expect(figures.getByText('Tier')).toBeInTheDocument()
  })

  it('AC2: the projected line is one table row with eleven cells, no orphans', async () => {
    const d = await open()
    const table = d.getByRole('table', { name: 'Projected per game' })
    expect(within(table).getAllByRole('columnheader')).toHaveLength(11)
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(2) // header + values
    expect(within(rows[1] as HTMLElement).getAllByRole('cell')).toHaveLength(11)
    expect(within(table).getByText('28.0')).toBeInTheDocument()
    expect(within(table).getByText('.820')).toBeInTheDocument()
  })

  it('AC1: percentile bars for nine categories against a full pool, TOV labelled', async () => {
    const d = await open(big)
    const bars = d.getAllByRole('meter')
    expect(bars).toHaveLength(9)
    expect(bars[0]).toHaveAccessibleName('PTS: 100th percentile')
    expect(d.getByText('TOV: higher = fewer turnovers')).toBeInTheDocument()
  })

  it('AC1: a small pool falls back to labelled strength bars', async () => {
    const d = await open() // the 10-player demo
    expect(d.queryAllByRole('meter')).toHaveLength(0)
    expect(d.getByText(/Standardized against the draft pool/)).toBeInTheDocument()
    expect(d.getByText('+2.80')).toBeInTheDocument()
  })

  it('AC3: indicators are a definition list with short reasons', async () => {
    const d = await open()
    const glance = within(d.getByRole('region', { name: 'At a glance' }))
    const terms = glance.getAllByRole('term')
    expect(terms.length).toBeGreaterThan(0)
    expect(glance.getAllByRole('definition')).toHaveLength(terms.length)
  })

  it('AC3: badges show under the name and their reasons follow the indicators', async () => {
    const d = await open()
    expect(within(d.getByTestId('detail-badges')).getAllByText(/Top tier/).length).toBe(1)
    expect(within(d.getByRole('list', { name: 'Badges' })).getByText(/Tier 1 of/)).toBeVisible()
  })
})
