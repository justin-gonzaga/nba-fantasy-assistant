import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from '../App'
import { ApiError } from '../api/http'
import type { ApiClient } from '../api/types'
import { E2E_EMAIL_KEY, e2eAuth } from '../auth/e2eAuth'

// WEB-008 AC4: a signed-in stranger (not invited) gets the dedicated no-access screen on every data
// tab — never data, never a generic error — and Sign out takes them back to the sign-in screen.
const forbidden = () =>
  Promise.reject(new ApiError(403, '/problems/forbidden', 'raw title from the API'))
const stranger: ApiClient = {
  today: forbidden,
  matchup: forbidden,
  waivers: forbidden,
  players: forbidden,
}

describe.each(['/today', '/matchup', '/waivers', '/players'])('no access on %s', (path) => {
  it('explains, names the account and offers Sign out', async () => {
    window.localStorage.setItem(E2E_EMAIL_KEY, 'stranger@example.test')
    render(<App client={stranger} sample={false} auth={e2eAuth()} initialPath={path} />)
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('This account doesn’t have access')
    expect(alert).toHaveTextContent('Sign out and use an invited account.')
    expect(alert).toHaveTextContent('Signed in as stranger@example.test.')
    expect(screen.queryByText('raw title from the API')).toBeNull()
    expect(screen.queryByText('Something went wrong on our side')).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByRole('list', { name: 'Players' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Retry' })).toBeNull()

    const card = alert.closest('.surface') as HTMLElement
    await userEvent.click(within(card).getByRole('button', { name: 'Sign out' }))
    expect(await screen.findByRole('button', { name: 'Sign in with Google' })).toBeInTheDocument()
    expect(window.localStorage.getItem(E2E_EMAIL_KEY)).toBeNull()
  })
})
