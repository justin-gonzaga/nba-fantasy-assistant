import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import { fixtureClient } from '../api/fixtures'
import { httpClient } from '../api/http'
import type { AuthAdapter } from './auth'
import { firebaseConfigFromEnv } from './firebase'

function fakeAuth() {
  let listener: (email: string | null) => void = () => {}
  const adapter: AuthAdapter = {
    subscribe(cb) {
      listener = cb
      cb(null)
      return () => {}
    },
    signIn: vi.fn(() => {
      listener('owner@example.com')
      return Promise.resolve()
    }),
    signOut: vi.fn(() => {
      listener(null)
      return Promise.resolve()
    }),
    token: () => Promise.resolve('id-token'),
  }
  return adapter
}

describe('sign-in (live mode)', () => {
  it('asks for Google sign-in, then shows the app with the account and a sign-out', async () => {
    const auth = fakeAuth()
    render(<App client={fixtureClient} sample={false} auth={auth} initialPath="/waivers" />)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in with Google' }))
    expect(auth.signIn).toHaveBeenCalled()
    expect(await screen.findByRole('list')).toBeInTheDocument()
    expect(screen.getByText(/Signed in as owner@example.com/)).toBeInTheDocument()
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    })
    expect(screen.getByRole('button', { name: 'Sign in with Google' })).toBeInTheDocument()
  })

  it('shows a failed sign-in', async () => {
    const auth = { ...fakeAuth(), signIn: () => Promise.reject(new Error('Popup closed')) }
    render(<App client={fixtureClient} sample={false} auth={auth} initialPath="/today" />)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in with Google' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Popup closed')
  })

  it('demo mode needs no sign-in', async () => {
    render(<App client={fixtureClient} auth={null} initialPath="/waivers" />)
    expect(await screen.findByRole('list')).toBeInTheDocument()
  })
})

describe('the API client in live mode', () => {
  it('sends the sign-in token as a bearer header', async () => {
    const seen: Headers[] = []
    const fetcher: typeof fetch = (_input, init) => {
      seen.push(new Headers(init?.headers))
      return Promise.resolve(new Response('{}', { status: 200 }))
    }
    await httpClient('https://api.test', fetcher, () => Promise.resolve('id-token')).today()
    expect(seen[0]?.get('Authorization')).toBe('Bearer id-token')
  })
})

describe('Firebase web config', () => {
  it('is complete or absent', () => {
    const full = {
      VITE_FIREBASE_API_KEY: 'k',
      VITE_FIREBASE_AUTH_DOMAIN: 'p.firebaseapp.com',
      VITE_FIREBASE_PROJECT_ID: 'p',
      VITE_FIREBASE_APP_ID: 'a',
    }
    expect(firebaseConfigFromEnv(full)?.projectId).toBe('p')
    expect(firebaseConfigFromEnv({ ...full, VITE_FIREBASE_APP_ID: '' })).toBeNull()
  })
})
