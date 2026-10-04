import { act, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from './App'
import { fixtureClient, samplePlayers } from './api/fixtures'
import type { ApiClient, PlayerRow } from './api/types'
import values from './features/draft/fixtures/values-2026-27.json'
import { CATEGORIES } from './features/players/format'

describe('Today (variant B: scoreboard first)', () => {
  it('shows all nine categories with an icon-and-word status, then the actions', async () => {
    render(<App initialPath="/today" />)
    const table = await screen.findByRole('table', { name: /projected category results/i })
    expect(within(table).getAllByRole('row')).toHaveLength(10) // header + 9 categories
    expect(within(table).getAllByText(/Winning|Losing|Toss-up/)).toHaveLength(9)
    expect(screen.getByRole('heading', { name: 'Do today' })).toBeInTheDocument()
    expect(screen.getByText('Sample data')).toBeInTheDocument()
    expect(screen.getByText(/Updated .* injury report/)).toBeInTheDocument()
  })

  it('opens an action to show its why', async () => {
    render(<App initialPath="/today" />)
    const row = await screen.findByRole('button', { name: /Add Jalen Smith/ })
    expect(row).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(row)
    expect(row).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Why')).toBeInTheDocument()
    expect(screen.getByText(/he adds 1.1/)).toBeInTheDocument()
  })
})

describe('navigation', () => {
  it('moves between tabs', async () => {
    render(<App initialPath="/today" />)
    await screen.findByRole('table')
    await userEvent.click(screen.getByRole('link', { name: 'Matchup' }))
    expect(await screen.findByText('5.2 of 9')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Matchup' })).toHaveAttribute('aria-current', 'page')
  })

  it('redirects the root to Today', async () => {
    render(<App initialPath="/" />)
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })
})

describe('Matchup (variant A: category board)', () => {
  it('explains what moves a category when tapped', async () => {
    render(<App initialPath="/matchup" />)
    const blk = await screen.findByRole('button', { name: /BLK/ })
    await userEvent.click(blk)
    expect(within(blk).getByText(/about even/)).toBeInTheDocument()
  })
})

describe('Waivers (variant A: ranked list)', () => {
  it('ranks all candidates and filters by category', async () => {
    render(<App initialPath="/waivers" />)
    const list = await screen.findByRole('list')
    expect(within(list).getAllByRole('listitem')).toHaveLength(6)
    await userEvent.click(screen.getByRole('button', { name: 'BLK' }))
    expect(screen.getByRole('button', { name: 'BLK' })).toHaveAttribute('aria-pressed', 'true')
    expect(within(screen.getByRole('list')).getAllByRole('listitem')).toHaveLength(2)
  })
})

describe('query states', () => {
  it('shows an error when the API fails', async () => {
    const failing: ApiClient = {
      ...fixtureClient,
      today: () => Promise.reject(new Error('API down')),
    }
    render(<App client={failing} initialPath="/today" />)
    // WEB-016: a plain message and Retry; never the raw error text as the headline
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Something went wrong on our side')
    expect(alert).not.toHaveTextContent('API down')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('shows a loading state first', () => {
    const never: ApiClient = { ...fixtureClient, today: () => new Promise(() => {}) }
    render(<App client={never} initialPath="/today" />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
  })
})

describe('live mode', () => {
  it('hides the sample badge when reading the real API', async () => {
    render(<App client={fixtureClient} sample={false} initialPath="/waivers" />)
    await screen.findByRole('list')
    expect(screen.queryByText('Sample data')).not.toBeInTheDocument()
  })
})

describe('desktop shell (WEB-023)', () => {
  const stub = (wide: boolean) =>
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (q: string) =>
        ({
          matches: wide && q.includes('min-width'),
          media: q,
          addEventListener: () => {},
          removeEventListener: () => {},
        }) as unknown as MediaQueryList,
    )

  afterEach(() => vi.restoreAllMocks())

  it('shows a sidebar and no tab bar on wide screens', async () => {
    stub(true)
    render(<App initialPath="/today" />)
    await screen.findByRole('table')
    const nav = screen.getByRole('navigation', { name: 'Main' })
    expect(nav).toHaveAttribute('data-variant', 'sidebar')
    expect(within(nav).getAllByRole('link')).toHaveLength(5)
    expect(within(nav).getByRole('link', { name: 'Today' })).toHaveAttribute('aria-current', 'page')
  })

  it('keeps the bottom tab bar on phones', async () => {
    stub(false)
    render(<App initialPath="/today" />)
    await screen.findByRole('table')
    expect(screen.getByRole('navigation', { name: 'Main' })).toHaveAttribute('data-variant', 'tabs')
  })
})

describe('today desktop (WEB-026 AC1)', () => {
  const viewport = (width: number) =>
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (q: string) =>
        ({
          matches: Number(/min-width:\s*(\d+)px/.exec(q)?.[1] ?? Infinity) <= width,
          media: q,
          addEventListener: () => {},
          removeEventListener: () => {},
        }) as unknown as MediaQueryList,
    )

  afterEach(() => vi.restoreAllMocks())

  it('puts the actions left and the scoreboard right at 1280 px', async () => {
    viewport(1280)
    render(<App initialPath="/today" />)
    const table = await screen.findByRole('table', { name: /projected category results/i })
    const columns = screen.getByTestId('today-columns')
    const [left, right] = Array.from(columns.children) as [HTMLElement, HTMLElement]
    expect(columns.children).toHaveLength(2)
    expect(within(left).getByRole('heading', { name: 'Do today' })).toBeInTheDocument()
    expect(right).toContainElement(table)
  })

  it('keeps one column (scoreboard first) on phones', async () => {
    viewport(390)
    render(<App initialPath="/today" />)
    await screen.findByRole('table', { name: /projected category results/i })
    expect(screen.queryByTestId('today-columns')).toBeNull()
  })
})

describe('resizing across the breakpoint (WEB-028)', () => {
  /** A matchMedia whose width can change, notifying listeners like a real resize. */
  function viewport(initial: number) {
    let width = initial
    const listeners = new Set<() => void>()
    vi.spyOn(window, 'matchMedia').mockImplementation((q: string) => {
      const min = Number(/min-width:\s*(\d+)px/.exec(q)?.[1] ?? Infinity)
      return {
        get matches() {
          return min <= width
        },
        media: q,
        addEventListener: (_: string, cb: () => void) => listeners.add(cb),
        removeEventListener: (_: string, cb: () => void) => listeners.delete(cb),
      } as unknown as MediaQueryList
    })
    return {
      set(w: number) {
        width = w
        for (const cb of [...listeners]) cb()
      },
    }
  }

  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('crossing 840 px keeps the page: a practice draft stays in its room', async () => {
    const pool = values.players.map((v, i) => ({
      ...(samplePlayers.players[0] as PlayerRow),
      id: Number(v.id),
      name: `Player ${v.id}`,
      rank: i + 1,
      dollars: v.usd,
      badges: [],
      indicators: [],
      strengths: Object.fromEntries(CATEGORIES.map(([k], j) => [k, v.z[j] ?? 0])),
    }))
    const client: ApiClient = {
      ...fixtureClient,
      players: () => Promise.resolve({ ...samplePlayers, players: pool }),
    }
    const vp = viewport(1280)
    render(<App client={client} initialPath="/draft" />)
    fireEvent.click(await screen.findByRole('radio', { name: /Untimed/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Start practice draft' }))
    expect(await screen.findByText('Sale 1 of 224')).toBeInTheDocument()
    act(() => vp.set(390))
    expect(screen.getByRole('navigation', { name: 'Main' })).toHaveAttribute('data-variant', 'tabs')
    expect(screen.getByText('Sale 1 of 224')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Start practice draft' })).toBeNull()
    act(() => vp.set(1280))
    expect(screen.getByRole('navigation', { name: 'Main' })).toHaveAttribute(
      'data-variant',
      'sidebar',
    )
    expect(screen.getByText('Sale 1 of 224')).toBeInTheDocument()
  })
})
