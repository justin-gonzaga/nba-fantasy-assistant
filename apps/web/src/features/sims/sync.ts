// SIM-006: keeping sims with the account (SIM-005), with this browser as a fallback. A finished run or a new
// league is queued locally first, then uploaded; anything the API can't take yet (offline, a deploy) stays
// queued and goes up on a later load. Saving is idempotent by id, so a retry never duplicates.

import { ApiError } from '../../api/http'
import type { SimIn, SimsApi } from '../../api/types'
import type { Report } from '../draft/report'
import type { SavedReport } from '../draft/ReportView'
import { loadHistory } from '../draft/report'
import type { ReplayLeague } from '../replay/league'

const PENDING = 'sims-pending-v1'
const MIGRATED = 'sims-migrated-v1'
const ETAGS = 'sims-etags-v1'
export const THIS_SEASON = '2026-27'

type Store = Pick<Storage, 'getItem' | 'setItem'>

function read<T>(key: string, fallback: T, storage: Store): T {
  try {
    const raw = storage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function write(key: string, value: unknown, storage: Store): void {
  try {
    storage.setItem(key, JSON.stringify(value))
  } catch {
    // storage blocked: the sim still uploads now if it can
  }
}

/** Ids the API accepts: letters, digits and `: _ . -`, at most 80. */
export const simId = (raw: string) => raw.replace(/[^A-Za-z0-9:_.-]/g, '-').slice(0, 80)

export function pending(storage: Store = localStorage): SimIn[] {
  return read<SimIn[]>(PENDING, [], storage)
}

export function enqueue(sim: SimIn, storage: Store = localStorage): void {
  const queue = pending(storage).filter((s) => s.id !== sim.id)
  write(PENDING, [...queue, sim], storage)
}

/** A 4xx other than 408/429 will never succeed: drop it. Anything else (offline, 5xx) is kept. */
const permanent = (e: unknown) =>
  e instanceof ApiError && e.status >= 400 && e.status < 500 && e.status !== 408 && e.status !== 429

export async function flush(api: SimsApi, storage: Store = localStorage): Promise<number> {
  let saved = 0
  for (const sim of pending(storage)) {
    try {
      const r = await api.save(sim)
      rememberEtag(r.sim.id, r.etag, storage)
      saved += 1
    } catch (e) {
      if (!permanent(e)) continue
    }
    write(
      PENDING,
      pending(storage).filter((s) => s.id !== sim.id),
      storage,
    )
  }
  return saved
}

export function rememberEtag(id: string, etag: string, storage: Store = localStorage): void {
  if (etag)
    write(ETAGS, { ...read<Record<string, string>>(ETAGS, {}, storage), [id]: etag }, storage)
}

export const knownEtag = (id: string, storage: Store = localStorage) =>
  read<Record<string, string>>(ETAGS, {}, storage)[id]

/** The practice runs kept before sims were saved to the account (DRAFT-015): uploaded once, as summaries. */
export function migrateHistory(storage: Store = localStorage): void {
  if (read(MIGRATED, false, storage)) return
  for (const h of loadHistory())
    enqueue(
      {
        id: simId(`run:${h.id || h.seed}`),
        kind: 'practice',
        season: THIS_SEASON,
        title: h.strategy,
        summary: { surplus: h.surplus, categoryWins: h.categoryWins, at: h.at },
        detail: {},
      },
      storage,
    )
  write(MIGRATED, true, storage)
}

export type RunSummary = {
  surplus: number
  categoryWins: number
  counted: number
  spent: number
  value: number
  at: string
}

export function runSim(
  runId: string,
  season: string | undefined,
  strategy: string,
  r: Report,
  saved: SavedReport,
  at: string,
): SimIn {
  const summary: RunSummary = {
    surplus: r.surplus,
    categoryWins: r.categoryWins,
    counted: r.categories.filter((c) => !c.punted).length,
    spent: r.spent,
    value: r.value,
    at,
  }
  return {
    id: simId(`run:${runId}`),
    kind: 'practice',
    season: season ?? THIS_SEASON,
    title: strategy,
    summary,
    detail: { version: 1, ...saved },
  }
}

export const leagueId = (l: ReplayLeague) => simId(`league:${l.season}:${l.savedAt}`)

export function leagueSummary(l: ReplayLeague) {
  const weeks = Object.values(l.results)
  const record = { wins: 0, losses: 0, ties: 0 }
  for (const w of weeks) {
    if (w.wins > w.losses) record.wins += 1
    else if (w.wins < w.losses) record.losses += 1
    else record.ties += 1
  }
  return { record, weeksKept: weeks.length }
}

export function leagueSim(l: ReplayLeague): SimIn {
  return {
    id: leagueId(l),
    kind: 'league',
    season: l.season,
    title: `${l.season} replay`,
    summary: leagueSummary(l),
    detail: l as unknown as Record<string, unknown>,
  }
}

const LEAGUES = 'sims-leagues-pending-v1'

/** Leagues whose latest progress hasn't reached the account yet (offline, a deploy), by sim id. */
export function pendingLeagues(storage: Store = localStorage): Record<string, ReplayLeague> {
  return read<Record<string, ReplayLeague>>(LEAGUES, {}, storage)
}

function markLeague(league: ReplayLeague | null, id: string, storage: Store): void {
  const rest = Object.fromEntries(Object.entries(pendingLeagues(storage)).filter(([k]) => k !== id))
  write(LEAGUES, league ? { ...rest, [id]: league } : rest, storage)
}

const weeksOf = (l: ReplayLeague | undefined) => Object.keys(l?.results ?? {}).length

/** One attempt to put this league on the account; throws when the API can't be reached. */
async function pushLeague(
  api: SimsApi,
  league: ReplayLeague,
  storage: Store,
): Promise<ReplayLeague> {
  const sim = leagueSim(league)
  const body = { title: sim.title, summary: sim.summary, detail: sim.detail }
  // Given the stored copy, either adopt it (it is further on) or write ours over it (CAS on its version).
  const settle = async (theirs: ReplayLeague | undefined, theirEtag: string) => {
    if (theirs && weeksOf(theirs) > weeksOf(league)) {
      rememberEtag(sim.id, theirEtag, storage)
      return theirs
    }
    if (JSON.stringify(theirs) === JSON.stringify(league)) {
      rememberEtag(sim.id, theirEtag, storage)
      return league
    }
    const r = await api.update(sim.id, body, theirEtag)
    rememberEtag(sim.id, r.etag, storage)
    return league
  }
  const etag = knownEtag(sim.id, storage)
  if (!etag) {
    const saved = await api.save(sim) // created now, or the stored copy if it exists
    return settle(saved.sim.detail as ReplayLeague | undefined, saved.etag)
  }
  try {
    const r = await api.update(sim.id, body, etag)
    rememberEtag(sim.id, r.etag, storage)
    return league
  } catch (e) {
    if (!(e instanceof ApiError) || (e.status !== 412 && e.status !== 404)) throw e
    if (e.status === 404) {
      // deleted elsewhere (or a reset store): save it afresh
      const saved = await api.save(sim)
      return settle(saved.sim.detail as ReplayLeague | undefined, saved.etag)
    }
    const current = (e.body as { current?: { detail?: ReplayLeague; version?: number } } | null)
      ?.current
    if (current?.version) return settle(current.detail, `"sim-v${current.version}"`)
    const fresh = await api.get(sim.id) // a 412 without the stored copy: read it, then decide
    return settle(fresh.sim.detail as ReplayLeague | undefined, fresh.etag)
  }
}

/**
 * A kept week, saved to the account. Two devices on one league: the copy with more kept weeks wins (the other
 * device's newer progress is never overwritten by an older copy). When the API can't be reached the league is
 * kept in a retry list and pushed the same way later (`flushLeagues`), never by a plain save, which would keep
 * the stale copy. Never throws; returns the league to continue with.
 */
export async function syncLeague(
  api: SimsApi,
  league: ReplayLeague,
  storage: Store = localStorage,
): Promise<ReplayLeague> {
  const id = leagueId(league)
  try {
    const out = await pushLeague(api, league, storage)
    markLeague(null, id, storage)
    return out
  } catch {
    markLeague(league, id, storage)
    return league
  }
}

/** Retries the leagues that didn't reach the account; returns how many did now. */
export async function flushLeagues(api: SimsApi, storage: Store = localStorage): Promise<number> {
  let done = 0
  for (const league of Object.values(pendingLeagues(storage))) {
    await syncLeague(api, league, storage)
    if (!pendingLeagues(storage)[leagueId(league)]) done += 1
  }
  return done
}
