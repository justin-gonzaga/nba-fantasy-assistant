import type { UseQueryResult } from '@tanstack/react-query'
import { useEffect, useState, type ReactNode } from 'react'
import { problemOf } from '../../api/problems'
import { useSession } from '../../auth/auth'
import { Button } from './Button'
import { Skeleton } from './Skeleton'
import { StateCard } from './StateCard'

/** After this long, the skeleton says the server may be waking up (Cloud Run cold start). */
export const SLOW_MS = 8000

export interface NotReady {
  title: string
  body: ReactNode
}

// Every query renders loading, slow, not-ready, error and ready states (frontend standard, WEB-016).
export function QueryState<T>({
  q,
  notReady,
  children,
}: {
  q: UseQueryResult<T>
  /** What this page says before its data exists (e.g. before the first brief). */
  notReady?: NotReady
  children: (d: T) => ReactNode
}) {
  const slow = useSlow(q.isPending)
  const refetch = q.refetch
  const failed = q.isError

  // Offline: try again as soon as the browser is back online.
  useEffect(() => {
    if (!failed) return
    const again = () => void refetch()
    window.addEventListener('online', again)
    return () => window.removeEventListener('online', again)
  }, [failed, refetch])

  if (q.isPending)
    return (
      <div role="status" className="flex flex-col gap-2 px-5 pt-5">
        <span className="sr-only">Loading…</span>
        {slow && (
          <p className="text-subhead text-muted">Still working… the server may be waking up.</p>
        )}
        <Skeleton className="mb-2 h-9 w-2/5" />
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    )
  if (q.isError)
    return (
      <div className="px-5 pt-5">
        <ProblemCard error={q.error} retry={() => void refetch()} notReady={notReady} />
      </div>
    )
  return <>{children(q.data)}</>
}

/** The state card for a failed request (WEB-016): not ready, sign-in, access, limits, server, offline. */
export function ProblemCard({
  error,
  retry,
  notReady,
}: {
  error: unknown
  retry: () => void
  notReady?: NotReady
}) {
  const session = useSession()
  const p = problemOf(error)
  return p.kind === 'not-ready' ? (
    <StateCard title={notReady?.title ?? 'Not published yet'}>
      {notReady?.body ?? 'This appears once the daily run publishes it.'}
    </StateCard>
  ) : (
    <StateCard
      tone={p.tone}
      title={p.title}
      action={
        p.action === 'retry' ? (
          <Button variant="secondary" onClick={retry}>
            Retry
          </Button>
        ) : (p.action === 'sign-in' || p.action === 'sign-out') && session ? (
          <Button variant="secondary" onClick={() => void session.signOut()}>
            {p.action === 'sign-in' ? 'Sign in again' : 'Sign out'}
          </Button>
        ) : undefined
      }
    >
      {p.body}
      {p.kind === 'forbidden' && session && <> Signed in as {session.email}.</>}
    </StateCard>
  )
}

function useSlow(pending: boolean): boolean {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    if (!pending) return
    const t = setTimeout(() => setSlow(true), SLOW_MS)
    return () => {
      clearTimeout(t)
      setSlow(false)
    }
  }, [pending])
  return slow
}
