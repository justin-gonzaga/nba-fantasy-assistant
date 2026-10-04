import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { Landing } from './Landing'

/** What the app needs from a sign-in provider (Firebase Auth in live mode; a fake in tests). */
export interface AuthAdapter {
  /** Calls back with the signed-in email, or null when signed out. Returns an unsubscribe. */
  subscribe(cb: (email: string | null) => void): () => void
  signIn(): Promise<void>
  signOut(): Promise<void>
  /** A fresh ID token for the API, or null when signed out. */
  token(): Promise<string | null>
}

interface Session {
  email: string
  signOut(): Promise<void>
}

const SessionContext = createContext<Session | null>(null)

/** The signed-in session (null in demo mode). */
export function useSession(): Session | null {
  return useContext(SessionContext)
}

/** Shows the landing (Google sign-in) until the adapter reports a signed-in user (D-27). */
export function SignInGate({
  adapter,
  onExplore,
  children,
}: {
  adapter: AuthAdapter
  /** WEB-026: the landing's "Explore with sample data". */
  onExplore?: () => void
  children: ReactNode
}) {
  const [email, setEmail] = useState<string | null | undefined>(undefined)
  useEffect(() => adapter.subscribe(setEmail), [adapter])

  if (email === undefined) {
    return (
      <p role="status" className="p-6 text-body text-muted">
        Checking sign-in…
      </p>
    )
  }
  if (email === null) return <Landing signIn={() => adapter.signIn()} onExplore={onExplore} />
  return (
    <SessionContext.Provider value={{ email, signOut: () => adapter.signOut() }}>
      {children}
    </SessionContext.Provider>
  )
}

/** WEB-026: sample mode inside the live build; `exit` returns to the landing. Null otherwise. */
export const SampleModeContext = createContext<{ exit: () => void } | null>(null)

export function useSampleMode() {
  return useContext(SampleModeContext)
}
