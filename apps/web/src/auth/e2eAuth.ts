import type { AuthAdapter } from './auth'

// WEB-008: the end-to-end tests' stand-in for Google sign-in. It is bundled only when the build sets
// VITE_E2E_AUTH=1 (see select.ts); normal builds tree-shake it out. The test chooses who is signed
// in by writing an email to localStorage before the page loads.
export const E2E_EMAIL_KEY = 'e2e-email'

/** A fake adapter: signed in as the stored email, signed out without one. */
export function e2eAuth(storage: Storage = window.localStorage): AuthAdapter {
  const listeners = new Set<(email: string | null) => void>()
  const current = () => storage.getItem(E2E_EMAIL_KEY)
  const emit = () => listeners.forEach((cb) => cb(current()))
  return {
    subscribe(cb) {
      listeners.add(cb)
      cb(current())
      return () => listeners.delete(cb)
    },
    signIn() {
      storage.setItem(E2E_EMAIL_KEY, 'owner@example.test')
      emit()
      return Promise.resolve()
    },
    signOut() {
      storage.removeItem(E2E_EMAIL_KEY)
      emit()
      return Promise.resolve()
    },
    token() {
      const email = current()
      return Promise.resolve(email ? `e2e-token:${email}` : null)
    },
  }
}
