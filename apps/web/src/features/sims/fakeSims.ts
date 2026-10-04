// An in-memory SimsApi for tests (the same rules as the API: idempotent save, CAS update, 404s).
import { ApiError } from '../../api/http'
import type { SimFull, SimIn, SimsApi, SimSummary } from '../../api/types'

export function fakeSims(opts: { offline?: boolean } = {}) {
  const sims = new Map<string, SimFull>()
  let clock = Date.parse('2026-10-04T10:00:00Z')
  const tag = (s: SimFull) => `"sim-v${s.version}"`
  const down = () => {
    if (state.offline) throw new TypeError('Failed to fetch')
  }
  const state = { offline: opts.offline ?? false, calls: [] as string[] }
  const summary = (s: SimFull): SimSummary => {
    const rest: Partial<SimFull> = { ...s }
    delete rest.detail
    return rest as SimSummary
  }
  const api: SimsApi = {
    list: () => {
      down()
      state.calls.push('list')
      return Promise.resolve(
        [...sims.values()].sort((a, b) => b.createdAt.localeCompare(a.createdAt)).map(summary),
      )
    },
    get: (id) => {
      down()
      const s = sims.get(id)
      if (!s) return Promise.reject(new ApiError(404, '/problems/not-found', 'No such sim'))
      return Promise.resolve({ sim: s, etag: tag(s) })
    },
    save: (sim: SimIn) => {
      down()
      state.calls.push(`save:${sim.id}`)
      const existing = sims.get(sim.id)
      if (existing) return Promise.resolve({ sim: existing, etag: tag(existing) })
      clock += 60_000
      const at = new Date(clock).toISOString()
      const s: SimFull = {
        ...sim,
        pinned: false,
        hasDetail: true,
        createdAt: at,
        updatedAt: at,
        version: 1,
      }
      sims.set(sim.id, s)
      return Promise.resolve({ sim: s, etag: tag(s) })
    },
    update: (id, body, etag) => {
      down()
      state.calls.push(`update:${id}`)
      const s = sims.get(id)
      if (!s) return Promise.reject(new ApiError(404, '/problems/not-found', 'No such sim'))
      if (etag !== tag(s))
        return Promise.reject(
          new ApiError(412, '/problems/stale-sim', 'Changed elsewhere', { current: s }),
        )
      const next = { ...s, ...body, version: s.version + 1 }
      sims.set(id, next)
      return Promise.resolve({ sim: next, etag: tag(next) })
    },
    pin: (id, pinned) => {
      down()
      const s = sims.get(id)
      if (!s) return Promise.reject(new ApiError(404, '/problems/not-found', 'No such sim'))
      if (pinned && !s.pinned && [...sims.values()].filter((x) => x.pinned).length >= 10)
        return Promise.reject(
          new ApiError(409, '/problems/too-many-pins', 'You can pin 10 runs: unpin one first.'),
        )
      const next = { ...s, pinned }
      sims.set(id, next)
      return Promise.resolve(summary(next))
    },
    remove: (id) => {
      down()
      state.calls.push(`remove:${id}`)
      if (!sims.delete(id))
        return Promise.reject(new ApiError(404, '/problems/not-found', 'No such sim'))
      return Promise.resolve()
    },
  }
  return { api, sims, state }
}
