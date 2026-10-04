import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../App'
import { fixtureClient } from '../api/fixtures'
import type { ApiClient } from '../api/types'
import type { AuthAdapter } from './auth'

function signedOut(over: Partial<AuthAdapter> = {}): AuthAdapter {
  return {
    subscribe(cb) {
      cb(null)
      return () => {}
    },
    signIn: vi.fn(() => Promise.resolve()),
    signOut: vi.fn(() => Promise.resolve()),
    token: () => Promise.resolve(null),
    ...over,
  }
}

/** A live client that must never be called while the visitor explores the sample. */
function liveSpy() {
  const calls: string[] = []
  const fail = (name: string) => () => {
    calls.push(name)
    return Promise.reject(new Error(`live ${name} called`))
  }
  const client: ApiClient = {
    ...fixtureClient,
    today: fail('today'),
    matchup: fail('matchup'),
    waivers: fail('waivers'),
    players: fail('players'),
  }
  return { client, calls }
}

afterEach(() => {
  sessionStorage.clear()
})

describe('landing (WEB-026 AC2)', () => {
  it('shows the hero, a preview, how it works and principles, with both actions', async () => {
    render(<App client={fixtureClient} sample={false} auth={signedOut()} initialPath="/today" />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in with Google' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Explore with sample data' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /preview of the players table/i })).toBeInTheDocument()
    const how = screen.getByRole('region', { name: 'How it works' })
    expect(within(how).getAllByRole('listitem')).toHaveLength(3)
    expect(screen.getByRole('region', { name: 'Principles' })).toBeInTheDocument()
  })

  it('shows a failed sign-in inline', async () => {
    const auth = signedOut({ signIn: () => Promise.reject(new Error('Popup closed')) })
    render(<App client={fixtureClient} sample={false} auth={auth} initialPath="/today" />)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in with Google' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Popup closed')
  })
})

describe('sample mode (WEB-026 AC3)', () => {
  it('opens the app on sample data with no live calls, and Sign in leaves it', async () => {
    const live = liveSpy()
    render(<App client={live.client} sample={false} auth={signedOut()} initialPath="/today" />)
    await userEvent.click(screen.getByRole('button', { name: 'Explore with sample data' }))
    expect(await screen.findByRole('table')).toBeInTheDocument() // the sample scoreboard
    expect(screen.getAllByText('Sample data').length).toBeGreaterThan(0)
    expect(live.calls).toEqual([])
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByRole('button', { name: 'Sign in with Google' })).toBeInTheDocument()
  })

  it('survives a refresh in the same tab', async () => {
    sessionStorage.setItem('sample-mode', '1')
    render(<App client={liveSpy().client} sample={false} auth={signedOut()} initialPath="/today" />)
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })
})

describe('no fabricated claims (WEB-026 AC4)', () => {
  it('has no user counts, ratings or testimonials', () => {
    const { container } = render(
      <App client={fixtureClient} sample={false} auth={signedOut()} initialPath="/today" />,
    )
    // The preview shows sample players; the claims live in the copy around it.
    const copy = Array.from(container.querySelectorAll('h1, h2, h3, p, li'))
      .filter((el) => !el.closest('[role="img"]'))
      .map((el) => el.textContent ?? '')
      .join(' ')
    expect(copy).not.toMatch(/\d[\d,.]*\+?\s*(users|managers|leagues|people|teams|downloads)/i)
    expect(copy).not.toMatch(/★|stars?\b|rated|testimonial/i)
    expect(container.querySelector('blockquote')).toBeNull()
  })
})
