// Response shapes, generated from the API's OpenAPI contract (APP-003):
// `pnpm api:types` rewrites schema.gen.ts from apps/api/openapi.json, and CI fails on drift.
import type { components } from './schema.gen'

type Schemas = components['schemas']

export type Freshness = Schemas['Freshness']
export type CategoryProjection = Schemas['CategoryProjection']
export type Action = Schemas['Action']
export type Matchup = Schemas['Matchup']
export type Today = Schemas['Today']
export type WaiverCandidate = Schemas['WaiverCandidate']
export type Waivers = Schemas['Waivers']
export type PlayerRow = Schemas['PlayerRow']
export type PlayerBadge = Schemas['Badge']
export type PlayerProjection = Schemas['PlayerProjection']
export type Players = Schemas['Players']
export type Confidence = NonNullable<Action['confidence']>
export type SimIn = Schemas['SimIn']
export type SimSummary = Schemas['SimSummary']
export type SimFull = Schemas['SimFull']
export type SimUpdate = Schemas['SimUpdate']

/** A sim with the ETag to update it with (If-Match). */
export type Versioned = { sim: SimFull; etag: string }

/** SIM-005: the signed-in user's saved sims. Absent on clients without an account (the demo). */
export interface SimsApi {
  list(): Promise<SimSummary[]>
  get(id: string): Promise<Versioned>
  /** Idempotent by `id`: saving a run again returns the stored copy. */
  save(sim: SimIn): Promise<Versioned>
  /** A replay league as it progresses; a 412 ApiError carries the stored copy in `body.current`. */
  update(id: string, sim: SimUpdate, etag: string): Promise<Versioned>
  pin(id: string, pinned: boolean): Promise<SimSummary>
  remove(id: string): Promise<void>
}

export interface ApiClient {
  today(): Promise<Today>
  matchup(): Promise<Matchup>
  waivers(): Promise<Waivers>
  players(variant: string): Promise<Players>
  /** SIM-001: the published replay seasons; absent on clients without season replay (demo). */
  replaySeasons?(): Promise<{ seasons: string[] }>
  /** SIM-001: one season's replay file (values, weeks, daily lines). */
  replaySeason?(season: string): Promise<unknown>
  sims?: SimsApi
}
