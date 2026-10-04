import type { ApiClient, Matchup, Players, SimFull, SimSummary, Today, Waivers } from './types'

/** An RFC 9457 problem from the API, surfaced with its title (never a stack trace). */
export class ApiError extends Error {
  readonly status: number
  readonly type: string
  /** The whole problem body (e.g. a 412's `current`). */
  readonly body: unknown

  constructor(status: number, type: string, title: string, body: unknown = null) {
    super(title)
    this.name = 'ApiError'
    this.status = status
    this.type = type
    this.body = body
  }
}

type TokenSource = () => Promise<string | null>
const sim = (id: string) => `/me/sims/${encodeURIComponent(id)}`
const noToken: TokenSource = () => Promise.resolve(null)

type Send = { method?: string; body?: unknown; headers?: Record<string, string> }

async function request<T>(
  base: string,
  path: string,
  fetcher: typeof fetch,
  token: TokenSource,
  send: Send = {},
): Promise<{ data: T; etag: string }> {
  const headers: Record<string, string> = { Accept: 'application/json', ...send.headers }
  const t = await token()
  if (t) headers.Authorization = `Bearer ${t}`
  if (send.body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetcher(`${base.replace(/\/$/, '')}${path}`, {
    headers,
    method: send.method ?? 'GET',
    ...(send.body !== undefined ? { body: JSON.stringify(send.body) } : {}),
  })
  if (!res.ok) {
    let type = 'about:blank'
    let title = `Request failed (${res.status})`
    let body: unknown = null
    try {
      body = await res.json()
      const problem = body as { type?: string; title?: string }
      type = problem.type ?? type
      title = problem.title ?? title
    } catch {
      // not a problem+json body: keep the status-based message
    }
    throw new ApiError(res.status, type, title, body)
  }
  const etag = res.headers.get('ETag') ?? ''
  const data = (res.status === 204 ? null : await res.json()) as T
  return { data, etag }
}

async function get<T>(
  base: string,
  path: string,
  fetcher: typeof fetch,
  token: TokenSource,
): Promise<T> {
  return (await request<T>(base, path, fetcher, token)).data
}

/** The live client: reads the API at `base` (e.g. https://…/api), sending the sign-in token. */
export function httpClient(
  base: string,
  fetcher: typeof fetch = fetch,
  token: TokenSource = noToken,
): ApiClient {
  return {
    today: () => get<Today>(base, '/today', fetcher, token),
    matchup: () => get<Matchup>(base, '/matchup', fetcher, token),
    waivers: () => get<Waivers>(base, '/waivers', fetcher, token),
    players: (variant) =>
      get<Players>(base, `/players?variant=${encodeURIComponent(variant)}`, fetcher, token),
    replaySeasons: () => get<{ seasons: string[] }>(base, '/replay/seasons', fetcher, token),
    replaySeason: (season) =>
      get<unknown>(base, `/replay/${encodeURIComponent(season)}`, fetcher, token),
    sims: {
      list: () => get<SimSummary[]>(base, '/me/sims', fetcher, token),
      get: async (id) => {
        const r = await request<SimFull>(base, sim(id), fetcher, token)
        return { sim: r.data, etag: r.etag }
      },
      save: async (body) => {
        const r = await request<SimFull>(base, '/me/sims', fetcher, token, { method: 'POST', body })
        return { sim: r.data, etag: r.etag }
      },
      update: async (id, body, etag) => {
        const r = await request<SimFull>(base, sim(id), fetcher, token, {
          method: 'PUT',
          body,
          headers: { 'If-Match': etag },
        })
        return { sim: r.data, etag: r.etag }
      },
      pin: async (id, pinned) =>
        (
          await request<SimSummary>(base, `${sim(id)}/pin`, fetcher, token, {
            method: 'PATCH',
            body: { pinned },
          })
        ).data,
      remove: async (id) => {
        await request<null>(base, sim(id), fetcher, token, { method: 'DELETE' })
      },
    },
  }
}
