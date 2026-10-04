import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import { fixtureClient, sampleMatchup, sampleToday, sampleWaivers } from '../api/fixtures'
import { ApiError } from '../api/http'
import type { ApiClient } from '../api/types'
import type { AuthAdapter } from '../auth/auth'
import { SLOW_MS } from '../components/ui/QueryState'

// WEB-016: the page × state table in the task file, one case per applicable cell.

type Page = 'today' | 'matchup' | 'waivers'
const PAGES: Page[] = ['today', 'matchup', 'waivers']
const NOT_READY: Record<Page, string> = {
  today: 'Your daily brief starts with the season',
  matchup: 'Your matchup appears once the season starts',
  waivers: 'Waiver picks start with the season',
}

const problem = (status: number, type: string) =>
  new ApiError(status, `/problems/${type}`, 'raw title from the API')

function failing(page: Page, err: unknown, calls = { n: 0 }): ApiClient {
  return {
    ...fixtureClient,
    [page]: () => {
      calls.n += 1
      return Promise.reject(err)
    },
  }
}

const signedIn: AuthAdapter = {
  subscribe: (cb) => {
    cb('owner@example.com')
    return () => {}
  },
  signIn: () => Promise.resolve(),
  signOut: vi.fn(() => Promise.resolve()),
  token: () => Promise.resolve('t'),
}

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

describe.each(PAGES)('%s states (AC3)', (page) => {
  it('not ready: explains what will appear, as a status (not an error)', async () => {
    render(<App client={failing(page, problem(404, 'no-brief'))} initialPath={`/${page}`} />)
    const status = await screen.findByText(NOT_READY[page])
    expect(status.closest('[role="status"]')).not.toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it.each([
    [401, 'unauthenticated', 'Your sign-in expired', 'Sign in again'],
    [403, 'forbidden', 'This account doesn’t have access', 'Sign out'],
  ])('%i: says what happened and offers %s', async (status, type, title, button) => {
    render(
      <App
        client={failing(page, problem(status, type))}
        auth={signedIn}
        initialPath={`/${page}`}
      />,
    )
    expect(await screen.findByText(title)).toBeInTheDocument()
    expect(screen.queryByText('raw title from the API')).toBeNull()
    const card = screen.getByText(title).closest('.surface') as HTMLElement
    await userEvent.click(within(card).getByRole('button', { name: button }))
    expect(signedIn.signOut).toHaveBeenCalled()
    if (status === 403) expect(card).toHaveTextContent('Signed in as owner@example.com.')
  })

  it.each([
    [429, 'rate-limited', 'Too many requests'],
    [500, 'internal', 'Something went wrong on our side'],
    [503, 'snapshot-schema', 'Something went wrong on our side'],
    [404, 'not-found', 'This part is being updated'],
  ])('%i %s: a message and Retry that refetches', async (status, type, title) => {
    const calls = { n: 0 }
    render(<App client={failing(page, problem(status, type), calls)} initialPath={`/${page}`} />)
    expect(await screen.findByText(title)).toBeInTheDocument()
    const before = calls.n
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(calls.n).toBeGreaterThan(before)
  })

  it('offline: says so and retries when the browser is back online', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    const calls = { n: 0 }
    render(
      <App
        client={failing(page, new TypeError('Failed to fetch'), calls)}
        initialPath={`/${page}`}
      />,
    )
    expect(await screen.findByText('You’re offline')).toBeInTheDocument()
    const before = calls.n
    await act(async () => {
      window.dispatchEvent(new Event('online'))
      await Promise.resolve()
    })
    expect(calls.n).toBeGreaterThan(before)
  })

  it('slow: the skeleton says the server may be waking up after 8 s', () => {
    vi.useFakeTimers()
    const never = { ...fixtureClient, [page]: () => new Promise(() => {}) }
    render(<App client={never} initialPath={`/${page}`} />)
    expect(screen.queryByText(/server may be waking up/)).toBeNull()
    act(() => {
      vi.advanceTimersByTime(SLOW_MS + 10)
    })
    expect(screen.getByText(/server may be waking up/)).toBeInTheDocument()
  })
})

describe('stale and empty states (AC3, AC4)', () => {
  const stale = { ...sampleToday.freshness, staleSince: '2026-10-20' }

  it.each([
    [
      'today',
      { ...fixtureClient, today: () => Promise.resolve({ ...sampleToday, freshness: stale }) },
    ],
    [
      'matchup',
      { ...fixtureClient, matchup: () => Promise.resolve({ ...sampleMatchup, freshness: stale }) },
    ],
    [
      'waivers',
      { ...fixtureClient, waivers: () => Promise.resolve({ ...sampleWaivers, freshness: stale }) },
    ],
  ] as [Page, ApiClient][])('%s shows the stale notice', async (page, client) => {
    render(<App client={client} initialPath={`/${page}`} />)
    expect(await screen.findByText('Data from Tue 20 Oct')).toBeInTheDocument()
    expect(screen.getByText(/NBA update didn’t run/)).toBeInTheDocument()
  })

  it('no stale notice when the data is fresh', async () => {
    render(<App initialPath="/today" />)
    await screen.findByRole('table')
    expect(screen.queryByText(/NBA update didn’t run/)).toBeNull()
  })

  it('Today with nothing to do says the lineup is set', async () => {
    const client = {
      ...fixtureClient,
      today: () => Promise.resolve({ ...sampleToday, actions: [] }),
    }
    render(<App client={client} initialPath="/today" />)
    expect(await screen.findByText('Nothing to do today: your lineup is set.')).toBeInTheDocument()
  })

  it('Waivers with no candidates says so', async () => {
    const client = {
      ...fixtureClient,
      waivers: () => Promise.resolve({ ...sampleWaivers, candidates: [] }),
    }
    render(<App client={client} initialPath="/waivers" />)
    expect(await screen.findByText('No free agent helps your team this week.')).toBeInTheDocument()
  })

  it('Matchup with no opponent is a neutral status', async () => {
    render(<App client={failing('matchup', problem(404, 'no-matchup'))} initialPath="/matchup" />)
    const s = await screen.findByText('No matchup this week')
    expect(s.closest('[role="status"]')).not.toBeNull()
  })

  it('Ask is a coming-soon card under the shared header', async () => {
    render(<App initialPath="/ask" />)
    expect(screen.getByRole('heading', { level: 1, name: 'Ask' })).toBeInTheDocument()
    expect(await screen.findByText('Coming soon')).toBeInTheDocument()
  })
})

describe('crashes and unknown pages (AC5)', () => {
  it('a page that throws shows the crash card and keeps the tab bar', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const broken = { ...fixtureClient, today: () => Promise.resolve({} as never) }
    render(<App client={broken} initialPath="/today" />)
    expect(await screen.findByText('This page hit a problem')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reload' })).toBeInTheDocument()
    expect(
      within(screen.getByRole('navigation', { name: 'Main' })).getByRole('link', {
        name: 'Players',
      }),
    ).toBeInTheDocument()
  })

  it('an unknown address shows Not found with the tab bar', () => {
    render(<App initialPath="/nope" />)
    expect(screen.getByText('Page not found')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Go to Today' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
  })
})

describe('demo mode (cross-cutting)', () => {
  it.each(['/today', '/matchup', '/waivers', '/players', '/ask'])(
    '%s in sample mode never shows a problem state',
    async (path) => {
      render(<App initialPath={path} />)
      expect(await screen.findAllByText('Sample data')).not.toHaveLength(0)
      expect(screen.queryByRole('alert')).toBeNull()
      expect(screen.queryByRole('button', { name: 'Retry' })).toBeNull()
    },
  )
})
