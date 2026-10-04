import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import type { ApiClient, PlayerRow, Players } from '../../api/types'
import { CATEGORIES } from '../players/format'
import { replayDoc } from '../replay/fixtures/replaySeason'
import values from './fixtures/values-2026-27.json'
import { myAdvice, SAVE_KEY, start, toDraftPlayers } from './practice'

const base = samplePlayers.players[0] as PlayerRow
const rows: PlayerRow[] = values.players.map((v, i) => ({
  ...base,
  id: Number(v.id),
  name: `Player ${v.id}`,
  rank: i + 1,
  dollars: v.usd,
  badges: [],
  indicators: [],
  strengths: Object.fromEntries(CATEGORIES.map(([k], j) => [k, v.z[j] ?? 0])),
}))
const full: Players = { ...samplePlayers, players: rows }

function spyClient() {
  const calls: string[] = []
  const client: ApiClient = {
    ...fixtureClient,
    today: () => (calls.push('today'), fixtureClient.today()),
    matchup: () => (calls.push('matchup'), fixtureClient.matchup()),
    waivers: () => (calls.push('waivers'), fixtureClient.waivers()),
    players: (v) => (calls.push(`players:${v}`), Promise.resolve(full)),
  }
  return { client, calls }
}

const SEED_RANDOM = 0.123
const seed = Math.floor(SEED_RANDOM * 1_000_000_000)

async function startDraft(pace: 'Real timers' | 'Untimed' = 'Untimed') {
  render(<App client={spyClient().client} initialPath="/draft" />)
  fireEvent.click(await screen.findByRole('radio', { name: new RegExp(pace) }))
  fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
}

beforeEach(() => {
  vi.spyOn(Math, 'random').mockReturnValue(SEED_RANDOM)
  localStorage.clear()
})
afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('glanceable, roster-aware room (DRAFT-016)', () => {
  it('AC1: the lot shows a headshot, a verdict with its state and a fit line', async () => {
    await startDraft()
    const verdictBox = await screen.findByTestId('verdict')
    expect(verdictBox.textContent).toMatch(
      /^(Good buy: bid up to \$\d+|Near your limit: up to \$\d+|Pass: over your \$\d+ ceiling|You can't bid on him)/,
    )
    expect(verdictBox.textContent).toMatch(/Fits your|Overlaps your team|Neutral fit/)
    const block = screen.getByRole('region', { name: /On the block/ })
    expect(block.querySelector('img')).not.toBeNull() // the headshot
  })

  it('AC5: recommendations on every lot, and the next best if you pass', async () => {
    await startDraft()
    const block = await screen.findByRole('region', { name: /On the block/ })
    const onBlock = within(block).getByText(/^Player \d+$/).textContent
    const recs = screen.getByRole('list', { name: 'Recommended for you' })
    const items = within(recs).getAllByRole('listitem')
    expect(items).toHaveLength(5)
    expect(items[0]?.textContent).toMatch(/up to \$\d+/)
    for (const li of items) expect(li.textContent).not.toContain(onBlock as string)
    expect(screen.getByTestId('if-you-pass')).toHaveTextContent(
      /^If you pass: next best is Player \d+, up to \$\d+\.$/,
    )
  })

  it('AC6: each rival opens its roster', async () => {
    await startDraft()
    fireEvent.click(await screen.findByRole('button', { name: /^Pass$/ }))
    const sale = within(screen.getByRole('list', { name: 'Recent sales' })).getAllByRole(
      'listitem',
    )[0]
    const team = /→ (Team \d+)/.exec(sale?.textContent ?? '')?.[1] as string
    const rivals = screen.getByRole('list', { name: 'Rivals' })
    const toggle = within(rivals).getByRole('button', { name: new RegExp(`^${team}(?!\\d)`) })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    const roster = screen.getByRole('list', { name: `${team} roster` })
    expect(within(roster).getAllByRole('listitem')).toHaveLength(1)
  })

  it('AC2: the needs panel starts empty and names categories once you own players', async () => {
    await startDraft()
    expect(await screen.findByText('Draft anyone: no needs yet.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sim to my next nomination' }))
    await screen.findByText('Your nomination')
    const team = screen.getByRole('region', { name: /Your team/ })
    if (within(team).queryByText('No players yet.') === null)
      expect(screen.getByTestId('needs').textContent).toMatch(/PTS|REB|AST|STL|BLK|3PM|FG%|FT%|TOV/)
  })
})

describe('draft practice page (DRAFT-014)', () => {
  it('AC2: shows the same ceiling and max bid as the draft-night advice', async () => {
    await startDraft()
    const expected = start(toDraftPlayers(rows), {
      seed,
      styles: 'mix',
      punted: null,
      pace: 'untimed',
    })
    expect(expected.phase).toBe('lot') // this seed opens on a rival's nomination
    const pid = expected.lot?.pid as string
    const ceiling = myAdvice(expected).players[pid]?.ceiling
    const block = await screen.findByRole('region', { name: /On the block/ })
    expect(within(block).getByText(`Player ${pid}`)).toBeInTheDocument()
    // the verdict states the same ceiling the engine computes (DRAFT-016 keeps the numbers)
    expect(screen.getByTestId('verdict')).toHaveTextContent(`$${ceiling}`)
    expect(screen.getByText(/Your max bid: \$187/)).toBeInTheDocument()
  })

  it('AC2: blocks a bid over the max bid with the reason', async () => {
    await startDraft()
    fireEvent.change(await screen.findByRole('textbox', { name: 'Custom bid in dollars' }), {
      target: { value: '300' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Bid' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Your max bid is $187')
  })

  it('AC3: with real timers, an expired bid timer sells the lot', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await startDraft('Real timers')
    await screen.findByText('Current bid')
    expect(screen.getByText('Nothing sold yet.')).toBeInTheDocument()
    await act(async () => {
      vi.advanceTimersByTime(21_000)
    })
    expect(
      within(screen.getByRole('list', { name: 'Recent sales' })).getAllByRole('listitem'),
    ).toHaveLength(1)
  })

  it('AC3: "Sim the rest" finishes with a 14-player team', async () => {
    await startDraft()
    fireEvent.click(await screen.findByRole('button', { name: 'Sim the rest' }))
    expect(await screen.findByText('Practice draft complete')).toBeInTheDocument()
    const table = screen.getByRole('table', { name: 'Your drafted team' })
    expect(within(table).getAllByRole('row')).toHaveLength(15) // header + 14
  }, 30_000)

  it('AC3: an unfinished draft can be resumed', async () => {
    const first = render(<App client={spyClient().client} initialPath="/draft" />)
    fireEvent.click(await screen.findByRole('radio', { name: /Untimed/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
    fireEvent.click(await screen.findByRole('button', { name: /Pass/ }))
    expect(localStorage.getItem(SAVE_KEY)).toContain('"sales":[{')
    first.unmount()
    render(<App client={spyClient().client} initialPath="/draft" />)
    expect(
      await screen.findByText(
        (_, el) =>
          el?.tagName === 'P' && el.textContent === 'An unfinished practice draft: 1 of 224 sold.',
      ),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Resume' }))
    const recent = await screen.findByRole('list', { name: 'Recent sales' })
    expect(within(recent).getAllByRole('listitem')).toHaveLength(1)
  })

  it('AC4: reads the player values only (no other API calls)', async () => {
    const spy = spyClient()
    render(<App client={spy.client} initialPath="/draft" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Start practice draft' }))
    await screen.findByText('Draft practice', { selector: 'h1' })
    expect(spy.calls).toEqual(['players:all'])
  })

  it('explains that the 10-player sample cannot run a practice auction', async () => {
    render(<App initialPath="/draft" />)
    expect(await screen.findByText('Practice needs the full player pool')).toBeInTheDocument()
  })
})

describe('replay season (SIM-002 AC1)', () => {
  it('offers this season and the published replay seasons, and drafts on that season’s values', async () => {
    const asked: string[] = []
    const client: ApiClient = {
      ...spyClient().client,
      replaySeasons: () => Promise.resolve({ seasons: ['2024-25'] }),
      replaySeason: (s) => (asked.push(s), Promise.resolve(replayDoc(s))),
    }
    render(<App client={client} initialPath="/draft" />)
    const select = await screen.findByRole('combobox', { name: 'Season' })
    const option = await within(select).findByRole('option', { name: 'Replay 2024-25' })
    expect(option).not.toBeDisabled()
    expect(
      within(select).getByRole('option', { name: 'Replay 2023-24 (not published yet)' }),
    ).toBeDisabled()
    expect(within(select).getByRole('option', { name: 'This season (2026-27)' })).toBeEnabled()
    fireEvent.change(select, { target: { value: '2024-25' } })
    fireEvent.click(screen.getByRole('radio', { name: /Untimed/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
    expect(await screen.findByText(/^2024-25 replay · Sale 1 of 224$/)).toBeInTheDocument()
    expect(asked).toEqual(['2024-25'])
    expect(screen.getAllByText(/^Replay \d+$/).length).toBeGreaterThan(0) // the season's names
    const saved = JSON.parse(localStorage.getItem(SAVE_KEY) ?? '{}') as {
      settings: { season?: string }
    }
    expect(saved.settings.season).toBe('2024-25')
  }, 30_000)

  it('a season that fails to load says why and stays on setup', async () => {
    const client: ApiClient = {
      ...spyClient().client,
      replaySeasons: () => Promise.resolve({ seasons: ['2024-25'] }),
      replaySeason: () => Promise.reject(new Error('offline')),
    }
    render(<App client={client} initialPath="/draft" />)
    const select = await screen.findByRole('combobox', { name: 'Season' })
    await within(select).findByRole('option', { name: 'Replay 2024-25' })
    fireEvent.change(select, { target: { value: '2024-25' } })
    fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Couldn't load the 2024-25 season (offline)",
    )
    expect(screen.getByRole('button', { name: 'Start practice draft' })).toBeEnabled()
  })
})
