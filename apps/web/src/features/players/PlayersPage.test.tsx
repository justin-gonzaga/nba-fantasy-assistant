import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../../App'
import { fixtureClient, samplePlayers } from '../../api/fixtures'
import { ApiError } from '../../api/http'
import type { ApiClient, PlayerRow, Players } from '../../api/types'

const base = samplePlayers.players[0] as PlayerRow

function row(i: number, over: Partial<PlayerRow> = {}): PlayerRow {
  return { ...base, id: 1000 + i, rank: i + 1, name: `Player ${i + 1}`, dollars: 200 - i, ...over }
}

function clientWith(
  players: (variant: string) => Promise<Players>,
  seen: string[] = [],
): ApiClient {
  return {
    ...fixtureClient,
    players: (v) => {
      seen.push(v)
      return players(v)
    },
  }
}

const many: Players = {
  ...samplePlayers,
  players: Array.from({ length: 120 }, (_, i) => row(i)),
}

const listItems = () =>
  within(screen.getByRole('list', { name: 'Players' })).getAllByRole('listitem')

describe('Players: list (AC3)', () => {
  it('is a tab and lists ranked players with value, tier, team, positions and status', async () => {
    render(<App initialPath="/today" />)
    await userEvent.click(await screen.findByRole('link', { name: 'Players' }))
    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(10)
    const first = within(items[0] as HTMLElement)
    expect(first.getByText('Nikola Jokić')).toBeInTheDocument()
    expect(first.getByText('DEN · C')).toBeInTheDocument()
    expect(first.getByText('$71')).toBeInTheDocument()
    expect(first.getByText('Tier 1')).toBeInTheDocument()
    const giannis = within(items[3] as HTMLElement)
    expect(giannis.getByText('Questionable')).toBeInTheDocument()
    expect(screen.getByText('10 players')).toBeInTheDocument()
  })

  it('shows initials when a headshot fails to load', async () => {
    render(<App initialPath="/players" />)
    const items = await screen.findAllByRole('listitem')
    const img = (items[0] as HTMLElement).querySelector('img') as HTMLImageElement
    expect(img.src).toBe('https://cdn.nba.com/headshots/nba/latest/260x190/203999.png')
    fireEvent.error(img)
    expect((items[0] as HTMLElement).querySelector('img')).toBeNull()
    expect(within(items[0] as HTMLElement).getByText('NJ')).toBeInTheDocument()
  })

  it('omits team and status when they are unknown (pre-season)', async () => {
    const pre = {
      ...samplePlayers,
      players: [row(0, { team: null, positions: null, status: null })],
    }
    render(<App client={clientWith(() => Promise.resolve(pre))} initialPath="/players" />)
    const item = (await screen.findAllByRole('listitem'))[0] as HTMLElement
    expect(within(item).queryByText(/·/)).toBeNull()
    expect(within(item).queryByText(/Questionable|Out/)).toBeNull()
  })
})

describe('Players: search, filters, sort, strategy (AC4)', () => {
  it('finds a player ignoring case and accents', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search players' }), 'jokic')
    expect(listItems()).toHaveLength(1)
    expect(screen.getByText('Nikola Jokić')).toBeInTheDocument()
    expect(screen.getByText('1 of 10 players')).toBeInTheDocument()
  })

  it('filters by position, matching combined positions', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.click(screen.getByRole('button', { name: 'C' }))
    expect(screen.getByRole('button', { name: 'C' })).toHaveAttribute('aria-pressed', 'true')
    // Jokić C, Wembanyama F-C, Holmgren C-F, Sabonis F-C
    expect(listItems()).toHaveLength(4)
  })

  it('sorts by a category strength', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Sort' }), 'blk')
    expect(within(listItems()[0] as HTMLElement).getByText('Victor Wembanyama')).toBeInTheDocument()
  })

  it('low minutes: a category sort puts players under 20 min/game last (WEB-027)', async () => {
    const proj = base.projection as NonNullable<PlayerRow['projection']>
    const bench = row(0, {
      name: 'Bench Guy',
      strengths: { ...base.strengths, tov: 9 },
      projection: { ...proj, mpg: 6 },
    })
    const starter = row(1, { name: 'Starter', strengths: { ...base.strengths, tov: 1 } })
    const fringe = row(2, {
      name: 'Fringe',
      inPool: false,
      strengths: { ...base.strengths, tov: 8 },
    })
    const d = { ...samplePlayers, players: [bench, starter, fringe] }
    render(<App client={clientWith(() => Promise.resolve(d))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Sort' }), 'tov')
    expect(within(listItems()[0] as HTMLElement).getByText('Starter')).toBeInTheDocument()
    expect(within(listItems()[1] as HTMLElement).getByText('Bench Guy')).toBeInTheDocument() // then rank order
    expect(within(listItems()[2] as HTMLElement).getByText('Fringe')).toBeInTheDocument()
  })

  it('requests the chosen strategy and keeps the search', async () => {
    const seen: string[] = []
    render(<App client={clientWith(fixtureClient.players, seen)} initialPath="/players?q=jok" />)
    await screen.findAllByRole('listitem')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Strategy' }), 'punt_ast')
    await screen.findByRole('option', { name: 'Punt AST', selected: true })
    expect(seen).toEqual(['all', 'punt_ast'])
    expect(screen.getByRole('searchbox', { name: 'Search players' })).toHaveValue('jok')
    expect(listItems()).toHaveLength(1)
  })

  it('restores state from the URL and falls back from an unknown strategy', async () => {
    const seen: string[] = []
    render(
      <App
        client={clientWith(fixtureClient.players, seen)}
        initialPath="/players?variant=punt_everything&pos=G&sort=dollars"
      />,
    )
    await screen.findByRole('option', { name: 'All categories', selected: true })
    expect(seen).toEqual(['punt_everything', 'all'])
    expect(screen.getByRole('button', { name: 'G' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('combobox', { name: 'Sort' })).toHaveValue('dollars')
  })
})

describe('Players: detail (AC5)', () => {
  it('opens a dialog with the projection and strengths; Escape closes and returns focus', async () => {
    render(<App initialPath="/players" />)
    const items = await screen.findAllByRole('listitem')
    const open = within(items[0] as HTMLElement).getByRole('button')
    await userEvent.click(open)
    const dialog = screen.getByRole('dialog', { name: 'Nikola Jokić' })
    expect(within(dialog).getByText('28.0')).toBeInTheDocument() // PTS per game
    expect(within(dialog).getByText('.490')).toBeInTheDocument() // FG%
    expect(within(dialog).getByText('+2.80')).toBeInTheDocument() // AST strength
    expect(within(dialog).getByText('−1.40')).toBeInTheDocument() // TOV strength
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(open).toHaveFocus()
  })

  it('keeps Tab focus inside the dialog', async () => {
    render(<App initialPath="/players" />)
    const items = await screen.findAllByRole('listitem')
    await userEvent.click(within(items[0] as HTMLElement).getByRole('button'))
    const close = within(screen.getByRole('dialog')).getByRole('button', { name: 'Close' })
    expect(close).toHaveFocus()
    await userEvent.tab()
    expect(close).toHaveFocus() // the only control: Tab wraps to it
    await userEvent.tab({ shift: true })
    expect(close).toHaveFocus()
  })

  it('says when there is no projection', async () => {
    const none = { ...samplePlayers, players: [row(0, { projection: null })] }
    render(<App client={clientWith(() => Promise.resolve(none))} initialPath="/players" />)
    await userEvent.click(
      within((await screen.findAllByRole('listitem'))[0] as HTMLElement).getByRole('button'),
    )
    expect(within(screen.getByRole('dialog')).getByText('No projection yet')).toBeInTheDocument()
  })
})

describe('Players: states (AC6)', () => {
  it('explains when values are not published yet', async () => {
    const missing = () =>
      Promise.reject(new ApiError(404, '/problems/no-players', 'No player values published'))
    render(<App client={clientWith(missing)} initialPath="/players" />)
    expect(await screen.findByText(/aren’t published yet/)).toBeInTheDocument()
  })

  it('offers Retry on other errors and recovers', async () => {
    let calls = 0
    const flaky = () => {
      calls += 1
      return calls === 1
        ? Promise.reject(new ApiError(502, 'about:blank', 'Request failed (502)'))
        : fixtureClient.players('all')
    }
    render(<App client={clientWith(flaky)} initialPath="/players" />)
    await userEvent.click(await screen.findByRole('button', { name: 'Retry' }))
    expect(await screen.findAllByRole('listitem')).toHaveLength(10)
  })

  it('shows a loading state', () => {
    render(<App client={clientWith(() => new Promise(() => {}))} initialPath="/players" />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading players')
  })

  it('says when nothing matches and clears the filters', async () => {
    render(<App initialPath="/players?q=zzz" />)
    expect(await screen.findByText('No players match')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(listItems()).toHaveLength(10)
  })
})

describe('Players: paging (AC7)', () => {
  it('shows 50 at a time and resets when the filter changes', async () => {
    render(<App client={clientWith(() => Promise.resolve(many))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    expect(listItems()).toHaveLength(50)
    expect(screen.getByText('120 players')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Show more' }))
    expect(listItems()).toHaveLength(100)
    await userEvent.click(screen.getByRole('button', { name: 'Show more' }))
    expect(listItems()).toHaveLength(120)
    expect(screen.queryByRole('button', { name: 'Show more' })).toBeNull()
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search players' }), 'Player 1')
    expect(listItems()).toHaveLength(32) // 1, 10–19, 100–120
    await userEvent.clear(screen.getByRole('searchbox', { name: 'Search players' }))
    expect(listItems()).toHaveLength(50)
  })
})

describe('Players: healthy rank (WEB-019 AC3)', () => {
  const hurt = row(0, {
    name: 'Hurt Star',
    rank: 40,
    healthyRank: 8,
    healthyDollars: 45,
    projection: { ...(base.projection as NonNullable<PlayerRow['projection']>), games: 45 },
  })
  const steady = row(1, { name: 'Steady Guy', rank: 12, healthyRank: 15, healthyDollars: 30 })
  const data = { ...samplePlayers, players: [steady, hurt] }

  it('no longer hints the healthy rank in the row (WEB-018: injury badges replace it)', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    expect(screen.queryByText(/Healthy #/)).toBeNull() // 40 vs 8 used to show a hint
  })

  it('sorts by healthy rank', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Sort' }), 'healthy')
    expect(within(listItems()[0] as HTMLElement).getByText('Hurt Star')).toBeInTheDocument()
  })

  it('explains both ranks in the detail', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.click(within(listItems()[1] as HTMLElement).getByRole('button'))
    expect(
      within(screen.getByRole('dialog')).getByText(
        'Ranked #40 after expected missed games (45 of 82); #8 if he plays 72.',
      ),
    ).toBeInTheDocument()
  })

  it('hides everything healthy when the values file has no healthy rank', async () => {
    const old = { ...samplePlayers, players: [row(0, { healthyRank: null, healthyDollars: null })] }
    render(<App client={clientWith(() => Promise.resolve(old))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    expect(screen.queryByRole('option', { name: 'Healthy rank' })).toBeNull()
    await userEvent.click(within(listItems()[0] as HTMLElement).getByRole('button'))
    expect(within(screen.getByRole('dialog')).queryByText(/if he plays 72/)).toBeNull()
  })
})

describe('Players: badges (WEB-018 AC3)', () => {
  const rowOf = (name: string) =>
    listItems().find((li) => within(li).queryByText(name)) as HTMLElement

  it('shows at most two badges in a row by priority, then +N', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    const tatum = within(rowOf('Jayson Tatum'))
    expect(tatum.getByText('Out')).toBeInTheDocument() // injured today first
    expect(tatum.getByText('Missed time')).toBeInTheDocument()
    expect(tatum.queryByText('Bounce-back')).toBeNull()
    expect(tatum.getByText('+1')).toHaveTextContent('+1 more label')
    const chet = within(rowOf('Chet Holmgren'))
    expect(chet.getByText('Injury prone')).toBeInTheDocument()
    expect(chet.getByText('Bounce-back')).toBeInTheDocument()
    // his demo 'Bigger role' signal is the third label: it joins the overflow (one row cap)
    expect(chet.getByText('+1')).toHaveTextContent('+1 more label')
    expect(chet.queryByTestId('signal-chip')).toBeNull()
    expect(within(rowOf('Anthony Edwards')).queryByTestId('row-badges')).toBeNull()
  })

  it('lists every badge with its why line in the detail', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.click(within(rowOf('Jayson Tatum')).getByRole('button'))
    const list = within(within(screen.getByRole('dialog')).getByRole('list', { name: 'Badges' }))
    expect(list.getAllByRole('listitem')).toHaveLength(3)
    expect(list.getByText('Bounce-back')).toBeInTheDocument()
    expect(list.getByText("Out on today's report")).toBeInTheDocument()
    expect(list.getByText('Played 16 of 82 games last season')).toBeInTheDocument()
    expect(list.getByText('Bounce-back chance 38 % (top 20 %)')).toBeInTheDocument()
  })

  it('says which badge inputs are not published yet', async () => {
    const gaps = {
      ...samplePlayers,
      players: [row(0, { badges: [] })],
      badgeNotes: ['Breakout model not published'],
    }
    render(<App client={clientWith(() => Promise.resolve(gaps))} initialPath="/players" />)
    await userEvent.click(
      within((await screen.findAllByRole('listitem'))[0] as HTMLElement).getByRole('button'),
    )
    const dialog = within(screen.getByRole('dialog'))
    expect(dialog.getByText('No badges')).toBeInTheDocument()
    expect(dialog.getByText('Breakout model not published')).toBeInTheDocument()
  })

  it('filters by badges (any chosen) and combines with search', async () => {
    render(<App initialPath="/players" />)
    await screen.findAllByRole('listitem')
    const group = within(screen.getByRole('group', { name: 'Filter by badge' }))
    await userEvent.click(group.getByRole('button', { name: /^Bounce-back( \d+)?$/ }))
    expect(group.getByRole('button', { name: /^Bounce-back( \d+)?$/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(listItems()).toHaveLength(2) // Holmgren, Tatum
    expect(screen.getByText('2 of 10 players')).toBeInTheDocument()
    await userEvent.click(group.getByRole('button', { name: /^Missed time( \d+)?$/ }))
    expect(listItems()).toHaveLength(3) // + Antetokounmpo
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search players' }), 'tatum')
    expect(listItems()).toHaveLength(1)
    await userEvent.clear(screen.getByRole('searchbox', { name: 'Search players' }))
    await userEvent.click(group.getByRole('button', { name: /^Bounce-back( \d+)?$/ }))
    await userEvent.click(group.getByRole('button', { name: /^Missed time( \d+)?$/ }))
    expect(listItems()).toHaveLength(10)
  })

  it('restores the badge filter from the URL, with position', async () => {
    render(<App initialPath="/players?badge=injury_prone,bounce_back,bogus&pos=F" />)
    await screen.findAllByRole('listitem')
    const group = within(screen.getByRole('group', { name: 'Filter by badge' }))
    expect(group.getByRole('button', { name: /^Injury prone( \d+)?$/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(group.getByRole('button', { name: /^Bounce-back( \d+)?$/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    // no sample rookies: a chip that would match nobody is hidden (WEB-022)
    expect(group.queryByRole('button', { name: /^Rookie/ })).toBeNull()
    expect(listItems()).toHaveLength(2) // Holmgren C-F, Tatum F-G
  })

  it('clears the badge filter with the other filters', async () => {
    render(<App initialPath="/players?badge=rookie" />)
    expect(await screen.findByText('No players match')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(listItems()).toHaveLength(10)
  })
})

describe('Players: decision indicators (WEB-020 AC3)', () => {
  type Ind = NonNullable<PlayerRow['indicators']>[number]
  const role = (v: number): Ind => ({
    code: 'role',
    label: `${v > 0 ? 'Bigger' : 'Smaller'} role ${v > 0 ? '+' : '−'}${Math.abs(v).toFixed(1)} min`,
    tone: v > 0 ? 'win' : 'lose',
    why: `Projected ${(30 + v).toFixed(1)} min vs 30.0 last season`,
    signal: true,
    value: v,
  })
  const certainty = (level: string, spread: number): Ind => ({
    code: 'certainty',
    label: `${level} certainty`,
    tone: level === 'High' ? 'win' : 'warn',
    why: 'Games and minutes spread',
    signal: false,
    value: spread,
  })
  const steady: Ind = {
    code: 'consistency',
    label: 'Steady',
    tone: 'win',
    why: 'Weekly value varied ±0.8',
    signal: false,
    value: null,
  }
  const grower = row(0, {
    name: 'Grower',
    indicators: [role(4.1), certainty('Low', 0.5)],
    signal: role(4.1),
  })
  const sure = row(1, {
    name: 'Sure Thing',
    indicators: [certainty('High', 0.1), steady],
    signal: null,
  })
  const plain = row(2, { name: 'Plain', indicators: [], signal: null })
  const data = { ...samplePlayers, players: [grower, sure, plain] }

  it('shows at most one signal chip in a row', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    const [first, second] = listItems() as [HTMLElement, HTMLElement]
    expect(within(first).getAllByTestId('signal-chip')).toHaveLength(1)
    expect(within(first).getByText('Bigger role +4.1 min')).toBeInTheDocument()
    expect(within(second).queryByTestId('signal-chip')).toBeNull()
  })

  it('lists every indicator with its why in the detail', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.click(within(listItems()[1] as HTMLElement).getByRole('button'))
    const panel = within(screen.getByRole('region', { name: 'At a glance' }))
    expect(panel.getByText('High certainty')).toBeInTheDocument()
    expect(panel.getByText('Weekly value varied ±0.8')).toBeInTheDocument()
  })

  it('sorts by certainty and by role change', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Sort' }), 'certainty')
    expect(within(listItems()[0] as HTMLElement).getByText('Sure Thing')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Sort' }), 'role')
    expect(within(listItems()[0] as HTMLElement).getByText('Grower')).toBeInTheDocument()
  })

  it('filters by signal and keeps it in the URL', async () => {
    render(
      <App client={clientWith(() => Promise.resolve(data))} initialPath="/players?sig=steady" />,
    )
    await screen.findAllByRole('listitem')
    expect(screen.getByRole('button', { name: /^Steady( \d+)?$/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(listItems()).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: /^Bigger role( \d+)?$/ }))
    expect(listItems()).toHaveLength(2) // any of the chosen signals
  })

  it('hides indicator sorts and the panel when no indicators are published', async () => {
    const none = { ...samplePlayers, players: [plain] }
    render(<App client={clientWith(() => Promise.resolve(none))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    expect(screen.queryByRole('option', { name: 'Certainty' })).toBeNull()
    await userEvent.click(within(listItems()[0] as HTMLElement).getByRole('button'))
    expect(screen.queryByRole('region', { name: 'At a glance' })).toBeNull()
  })
})

describe('Players: one row priority for badges and signals (WEB-020 review)', () => {
  it('caps a row at two chips: badges first, the signal joins the "+N"', async () => {
    const sig = {
      code: 'role' as const,
      label: 'Bigger role +4.1 min',
      tone: 'win' as const,
      why: 'x',
      signal: true,
      value: 4.1,
    }
    const busy = row(0, {
      name: 'Busy',
      badges: [
        { code: 'injury_prone', label: 'Injury prone', tone: 'lose', why: 'a' },
        { code: 'rookie', label: 'Rookie', tone: 'neutral', why: 'b' },
      ],
      indicators: [sig],
      signal: sig,
    })
    render(
      <App
        client={clientWith(() => Promise.resolve({ ...samplePlayers, players: [busy] }))}
        initialPath="/players"
      />,
    )
    const item = (await screen.findAllByRole('listitem'))[0] as HTMLElement
    expect(within(item).getByText('Injury prone')).toBeInTheDocument()
    expect(within(item).queryByTestId('signal-chip')).toBeNull()
    expect(within(item).getByText('+1')).toBeInTheDocument()
  })
})

describe('Players: filters never dead-end (WEB-022 AC4)', () => {
  const prone = {
    code: 'injury_prone' as const,
    label: 'Injury prone',
    tone: 'lose' as const,
    why: 'x',
  }
  const data = {
    ...samplePlayers,
    badgeNotes: ['Breakout chance appears after the pre-season backfill (draft week)'],
    players: [
      row(0, { badges: [prone], indicators: [], signal: null }),
      row(1, { badges: [], indicators: [], signal: null }),
    ],
  }

  it('shows counts and hides chips that would match nobody', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    const group = within(screen.getByRole('group', { name: 'Filter by badge' }))
    expect(group.getByRole('button', { name: 'Injury prone 1' })).toBeInTheDocument()
    expect(group.queryByRole('button', { name: /Breakout/ })).toBeNull()
    expect(group.queryByRole('button', { name: /Rookie/ })).toBeNull()
  })

  it('says why a source is missing', async () => {
    render(<App client={clientWith(() => Promise.resolve(data))} initialPath="/players" />)
    await screen.findAllByRole('listitem')
    expect(
      screen.getByText('Breakout chance appears after the pre-season backfill (draft week)'),
    ).toBeInTheDocument()
  })

  it('keeps a selected chip visible even at zero (old links) so it can be cleared', async () => {
    render(
      <App client={clientWith(() => Promise.resolve(data))} initialPath="/players?badge=rookie" />,
    )
    expect(await screen.findByText('No players match')).toBeInTheDocument()
    const chip = screen.getByRole('button', { name: 'Rookie 0' })
    expect(chip).toHaveAttribute('aria-pressed', 'true')
  })
})
