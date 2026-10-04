import { ApiError } from '../../api/http'
import { HISTORY_KEY } from '../draft/report'
import type { ReplayLeague } from '../replay/league'
import { fakeSims } from './fakeSims'
import {
  enqueue,
  flush,
  flushLeagues,
  knownEtag,
  leagueSim,
  migrateHistory,
  pending,
  pendingLeagues,
  syncLeague,
} from './sync'

const memory = () => {
  const m = new Map<string, string>()
  return {
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
  }
}

const run = (id: string) => ({
  id,
  kind: 'practice' as const,
  season: '2026-27',
  title: 'All categories',
  summary: { surplus: 5 },
  detail: { version: 1 },
})

const league = (weeks: number): ReplayLeague => ({
  version: 1,
  season: '2024-25',
  me: 'me',
  rosters: { me: [1], 'Team 2': [2] },
  savedAt: '2026-10-04T10:00:00.000Z',
  results: Object.fromEntries(
    Array.from({ length: weeks }, (_, i) => [
      String(i + 1),
      { opponent: 'Team 2', wins: 5, losses: 4, ties: 0 },
    ]),
  ),
})

beforeEach(() => localStorage.clear())

describe('sync (SIM-006 AC3)', () => {
  it('queues a run and uploads it; offline it stays queued, then goes up later without duplicates', async () => {
    const s = memory()
    const fake = fakeSims({ offline: true })
    enqueue(run('run:a'), s)
    enqueue(run('run:a'), s) // the same run twice (StrictMode, a retry): queued once
    expect(pending(s)).toHaveLength(1)
    expect(await flush(fake.api, s)).toBe(0)
    expect(pending(s)).toHaveLength(1)
    fake.state.offline = false
    expect(await flush(fake.api, s)).toBe(1)
    expect(pending(s)).toEqual([])
    enqueue(run('run:a'), s)
    await flush(fake.api, s)
    expect(fake.sims.size).toBe(1)
  })

  it('a permanently refused sim leaves the queue (it would never succeed)', async () => {
    const s = memory()
    const fake = fakeSims()
    fake.api.save = () => Promise.reject(new (class extends Error {})()) // network-like: kept
    enqueue(run('run:b'), s)
    await flush(fake.api, s)
    expect(pending(s)).toHaveLength(1)
    const { ApiError } = await import('../../api/http')
    fake.api.save = () => Promise.reject(new ApiError(413, '/problems/too-large', 'Too large'))
    await flush(fake.api, s)
    expect(pending(s)).toEqual([])
  })

  it('migrates the browser’s run history once, as summaries', () => {
    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify([
        {
          id: '5:2026-10-01T09:00:00Z',
          at: '2026-10-01',
          seed: 5,
          strategy: 'Punt FT%',
          surplus: 7,
          categoryWins: 4.2,
        },
      ]),
    )
    const s = memory()
    migrateHistory(s)
    migrateHistory(s)
    expect(pending(s)).toHaveLength(1)
    expect(pending(s)[0]).toMatchObject({ kind: 'practice', title: 'Punt FT%', detail: {} })
    expect(pending(s)[0]?.id).toMatch(/^run:5:2026-10-01T09:00:00Z$/)
  })

  it('a league syncs as it progresses; the copy with more kept weeks wins between devices', async () => {
    const fake = fakeSims()
    const phone = memory()
    const desktop = memory()
    expect(await syncLeague(fake.api, league(0), phone)).toEqual(league(0))
    await syncLeague(fake.api, league(1), phone) // week 1 kept on the phone
    expect(fake.sims.get(leagueSim(league(1)).id)?.summary).toMatchObject({ weeksKept: 1 })
    // the desktop knows an old version: its stale copy (0 weeks) loses to the phone's (1 week)
    const adopted = await syncLeague(fake.api, league(0), desktop)
    expect(Object.keys(adopted.results)).toEqual(['1'])
    // the desktop plays on (2 weeks): it is ahead, so it overwrites
    await syncLeague(fake.api, league(2), desktop)
    expect(fake.sims.get(leagueSim(league(2)).id)?.summary).toMatchObject({ weeksKept: 2 })
    expect(knownEtag(leagueSim(league(2)).id, desktop)).toBe('"sim-v3"')
  })

  it('a week kept offline reaches the account later, through the merge (not a plain save)', async () => {
    const fake = fakeSims()
    const s = memory()
    await syncLeague(fake.api, league(2), s) // the account has 2 weeks
    fake.state.offline = true
    expect(await syncLeague(fake.api, league(3), s)).toEqual(league(3)) // week 3 kept offline
    expect(Object.keys(pendingLeagues(s))).toHaveLength(1)
    expect(await flush(fake.api, s)).toBe(0) // the run queue doesn't carry leagues
    fake.state.offline = false
    expect(await flushLeagues(fake.api, s)).toBe(1)
    expect(fake.sims.get(leagueSim(league(3)).id)?.summary).toMatchObject({ weeksKept: 3 })
    expect(pendingLeagues(s)).toEqual({})
  })

  it('a 412 without the stored copy reads it, then merges; a league deleted elsewhere is saved afresh', async () => {
    const fake = fakeSims()
    const s = memory()
    await syncLeague(fake.api, league(1), s)
    const id = leagueSim(league(1)).id
    const real = fake.api.update
    let first = true
    fake.api.update = (sid, body, etag) => {
      if (first) {
        first = false
        return Promise.reject(new ApiError(412, '/problems/stale-sim', 'stale', {}))
      }
      return real(sid, body, etag)
    }
    await syncLeague(fake.api, league(2), s)
    expect(fake.sims.get(id)?.summary).toMatchObject({ weeksKept: 2 })
    fake.api.update = real
    fake.sims.delete(id)
    await syncLeague(fake.api, league(3), s)
    expect(fake.sims.get(id)?.summary).toMatchObject({ weeksKept: 3 })
    expect(pendingLeagues(s)).toEqual({})
  })
})
