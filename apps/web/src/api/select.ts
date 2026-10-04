import type { AuthAdapter } from '../auth/auth'
import { e2eAuth } from '../auth/e2eAuth'
import { firebaseAuth, firebaseConfigFromEnv } from '../auth/firebase'
import { fixtureClient } from './fixtures'
import { httpClient } from './http'
import type { ApiClient } from './types'

// Live mode needs VITE_API_URL and the Firebase web config at build time: the owner signs in with
// Google (D-27) and every API call carries the ID token. Otherwise: the sample data (demo, D-38).
const env = import.meta.env as Record<string, string | undefined>
const url = env.VITE_API_URL ?? ''
const firebase = firebaseConfigFromEnv(env)
// WEB-008: end-to-end builds swap Google sign-in for a fake. Read straight from import.meta.env so
// Vite inlines the constant and normal builds drop this branch and the e2eAuth module.
const e2e = import.meta.env.VITE_E2E_AUTH === '1'

export const liveApiUrl: string | null = url.length > 0 && (e2e || firebase) ? url : null
export const defaultAuth: AuthAdapter | null =
  e2e && liveApiUrl ? e2eAuth() : liveApiUrl && firebase ? firebaseAuth(firebase) : null
export const defaultClient: ApiClient =
  liveApiUrl && defaultAuth
    ? httpClient(liveApiUrl, fetch, () => defaultAuth.token())
    : fixtureClient
