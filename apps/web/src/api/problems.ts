import { ApiError } from './http'

// WEB-016: every way a request can fail, mapped to one user-facing state. Copy is plain and
// never shows a stack trace or a bare status code as the headline.

export type ProblemKind =
  | 'not-ready'
  | 'no-matchup'
  | 'unauthenticated'
  | 'forbidden'
  | 'rate-limited'
  | 'updating'
  | 'offline'
  | 'server'

export type Tone = 'neutral' | 'warn' | 'error'
export type ProblemAction = 'retry' | 'sign-in' | 'sign-out' | 'none'

export interface Problem {
  kind: ProblemKind
  tone: Tone
  title: string
  body: string
  action: ProblemAction
}

const NOT_READY_TYPES = new Set(['no-brief', 'no-players'])

/** The problem-type slug of an RFC 9457 `type` ("/problems/no-brief" → "no-brief"). */
function slug(type: string): string {
  return type.split('/').filter(Boolean).pop() ?? ''
}

export function problemOf(error: unknown, online = navigator.onLine): Problem {
  if (!online || (error instanceof TypeError && !(error instanceof ApiError))) {
    return {
      kind: 'offline',
      tone: 'warn',
      title: online ? 'Can’t reach the server' : 'You’re offline',
      body: online
        ? 'Check your connection; we’ll try again.'
        : 'We’ll load this as soon as you’re back online.',
      action: 'retry',
    }
  }
  if (!(error instanceof ApiError)) {
    return server()
  }
  const kind = slug(error.type)
  if (error.status === 404 && NOT_READY_TYPES.has(kind)) {
    return { kind: 'not-ready', tone: 'neutral', title: '', body: '', action: 'none' }
  }
  if (error.status === 404 && kind === 'no-matchup') {
    return {
      kind: 'no-matchup',
      tone: 'neutral',
      title: 'No matchup this week',
      body: 'There’s no opponent scheduled this week (a bye or the pre-season).',
      action: 'none',
    }
  }
  if (error.status === 404) {
    // The route itself is missing: the site is newer than the API (a deploy in progress).
    return {
      kind: 'updating',
      tone: 'warn',
      title: 'This part is being updated',
      body: 'Try again in a few minutes.',
      action: 'retry',
    }
  }
  if (error.status === 401) {
    return {
      kind: 'unauthenticated',
      tone: 'warn',
      title: 'Your sign-in expired',
      body: 'Sign in again to continue.',
      action: 'sign-in',
    }
  }
  if (error.status === 403) {
    return {
      kind: 'forbidden',
      tone: 'error',
      title: 'This account doesn’t have access',
      body: 'Sign out and use an invited account.',
      action: 'sign-out',
    }
  }
  if (error.status === 429) {
    return {
      kind: 'rate-limited',
      tone: 'warn',
      title: 'Too many requests',
      body: 'Try again in a minute.',
      action: 'retry',
    }
  }
  return server()
}

function server(): Problem {
  return {
    kind: 'server',
    tone: 'error',
    title: 'Something went wrong on our side',
    body: 'It’s not you. Try again shortly.',
    action: 'retry',
  }
}
