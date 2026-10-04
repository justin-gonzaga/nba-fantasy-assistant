import { describe, expect, it, vi } from 'vitest'
import { E2E_EMAIL_KEY, e2eAuth } from './e2eAuth'

// WEB-008 AC2: the e2e auth seam signs in as the stored email, with no Google or Firebase.
function memoryStorage(): Storage {
  const m = new Map<string, string>()
  return {
    get length() {
      return m.size
    },
    clear: () => m.clear(),
    getItem: (k) => m.get(k) ?? null,
    key: (i) => [...m.keys()][i] ?? null,
    removeItem: (k) => void m.delete(k),
    setItem: (k, v) => void m.set(k, v),
  }
}

describe('e2eAuth', () => {
  it('reports the stored email and hands out a token for it', async () => {
    const s = memoryStorage()
    s.setItem(E2E_EMAIL_KEY, 'owner@example.test')
    const auth = e2eAuth(s)
    const cb = vi.fn()
    auth.subscribe(cb)
    expect(cb).toHaveBeenCalledWith('owner@example.test')
    expect(await auth.token()).toBe('e2e-token:owner@example.test')
  })

  it('is signed out without a stored email; sign in and out notify subscribers', async () => {
    const s = memoryStorage()
    const auth = e2eAuth(s)
    const cb = vi.fn()
    const stop = auth.subscribe(cb)
    expect(cb).toHaveBeenLastCalledWith(null)
    expect(await auth.token()).toBeNull()
    await auth.signIn()
    expect(cb).toHaveBeenLastCalledWith('owner@example.test')
    await auth.signOut()
    expect(cb).toHaveBeenLastCalledWith(null)
    expect(s.getItem(E2E_EMAIL_KEY)).toBeNull()
    stop()
    await auth.signIn()
    expect(cb).toHaveBeenCalledTimes(3)
  })
})
