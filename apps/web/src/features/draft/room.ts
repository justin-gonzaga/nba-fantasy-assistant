// DRAFT-013: a simulated auction room. 15 managers with styles nominate and bid around the published
// values, using the same arithmetic as the draft-night board (live.ts). Deterministic: every random
// choice hashes (seed, …), so a seed and the owner's actions replay the same room.
import {
  advise,
  categoryWeights,
  fitMultiplier,
  teamState,
  type DraftPlayer,
  type Sale,
  type TeamState,
} from './live'

export type Style = 'balanced' | 'stars' | 'punter' | 'value'
export const STYLES: readonly Style[] = ['balanced', 'stars', 'punter', 'value']
export const STYLE_LABEL: Record<Style, string> = {
  balanced: 'Balanced',
  stars: 'Stars and scrubs',
  punter: 'Punter',
  value: 'Value hunter',
}

export type Manager = { team: string; style: Style; punted: ReadonlySet<number>; human: boolean }

export type RoomConfig = {
  players: readonly DraftPlayer[]
  teams: readonly string[]
  /** The owner's team, or null for an all-simulated room (calibration, "sim the rest"). */
  me: string | null
  budget?: number
  slots?: number
  seed: number
  /** 'mix' gives each simulated manager a style by seed; a style gives all of them that one. */
  styles?: 'mix' | Style
  myPunted?: ReadonlySet<number>
}

export type Room = {
  players: readonly DraftPlayer[]
  teams: readonly string[]
  me: string | null
  budget: number
  slots: number
  seed: number
  managers: Record<string, Manager>
  sales: Sale[]
  /** Index into `teams` of the next nominator (skips full rosters). */
  turn: number
}

/** Tuning, fixed by the calibration test (AC2): see the task's Evidence. */
export const TUNING = {
  noise: 0.08, // each manager's private value = engine value × U(1 − noise, 1 + noise)
  starsTop: 1.12, // stars-and-scrubs pay up for players worth ≥ $35 …
  starsMid: 0.94, // … less for the middle …
  starsLow: 0.8, // … and little for ≤ $8 players
  valueHunter: 0.9,
  drainShare: 0.3, // share of nominations that are budget drains rather than the nominator's own target
  rich: 1, // walk-away × (1 + rich × (cash per open spot ÷ the room's − 1)) for richer-than-average teams …
  richCap: 1.6, // … capped
  pool: 60, // nominations consider the top N available by value
}

// --- deterministic randomness --------------------------------------------------------------------

/** A uniform number in [0, 1) from any key parts (FNV-1a then a mulberry32 step). */
export function hash01(...parts: (string | number)[]): number {
  let h = 2166136261
  for (const ch of parts.join('|')) {
    h ^= ch.charCodeAt(0)
    h = Math.imul(h, 16777619)
  }
  let t = (h + 0x6d2b79f5) | 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

// --- set-up --------------------------------------------------------------------------------------

export function createRoom(cfg: RoomConfig): Room {
  const managers: Record<string, Manager> = {}
  const order = [...STYLES].sort(
    (a, b) => hash01(cfg.seed, 'style', a) - hash01(cfg.seed, 'style', b),
  )
  cfg.teams.forEach((team, i) => {
    const human = team === cfg.me
    const style: Style = human
      ? 'balanced'
      : cfg.styles && cfg.styles !== 'mix'
        ? cfg.styles
        : (order[i % order.length] as Style)
    const n = cfg.players[0]?.z.length ?? 9
    const punted = human
      ? (cfg.myPunted ?? new Set<number>())
      : style === 'punter'
        ? new Set([Math.floor(hash01(cfg.seed, 'punt', team) * n)])
        : new Set<number>()
    managers[team] = { team, style, punted, human }
  })
  return {
    players: cfg.players,
    teams: cfg.teams,
    me: cfg.me,
    budget: cfg.budget ?? 200,
    slots: cfg.slots ?? 14,
    seed: cfg.seed,
    managers,
    sales: [],
    turn: Math.floor(hash01(cfg.seed, 'first') * cfg.teams.length),
  }
}

export const isComplete = (room: Room) =>
  Object.values(teamState(room.sales, room.teams, room.budget, room.slots)).every(
    (s) => s.open === 0,
  )

export const available = (room: Room) => {
  const taken = new Set(room.sales.map((s) => s.pid))
  return room.players.filter((p) => !taken.has(p.id))
}

// --- valuations ----------------------------------------------------------------------------------

type Context = {
  state: Record<string, TeamState>
  infl: number
  byId: ReadonlyMap<string, DraftPlayer>
  weights: Record<string, number[]>
  taken: ReadonlySet<string>
  /** The room's money per open roster spot (teams that can still buy). */
  perSlot: number
}

// A Map, not an object: NBA ids are numeric strings, which push a plain object into slow sparse mode.
type Index = { byId: Map<string, DraftPlayer>; sorted: DraftPlayer[] }
const indexes = new WeakMap<readonly DraftPlayer[], Index>()

/** Players by id and by value (descending), built once per player list. */
function indexOf(players: readonly DraftPlayer[]): Index {
  let ix = indexes.get(players)
  if (!ix) {
    const byId = new Map(players.map((p) => [p.id, p] as const))
    ix = { byId, sorted: [...players].sort((a, b) => b.usd - a.usd) }
    indexes.set(players, ix)
  }
  return ix
}

/** `inflation` from live.ts, on the presorted list (same result; the room calls it every lot). */
function fastInflation(
  sorted: readonly DraftPlayer[],
  taken: ReadonlySet<string>,
  state: Record<string, TeamState>,
): number {
  let money = 0
  let open = 0
  for (const st of Object.values(state)) {
    if (st.open > 0) money += st.left
    open += st.open
  }
  if (open <= 0) return 1
  let above = 0
  let n = 0
  for (const p of sorted) {
    if (n >= open) break
    if (taken.has(p.id)) continue
    above += Math.max(0, p.usd - 1)
    n += 1
  }
  if (above <= 0) return 1
  return Math.max(0, money - open) / above
}

/** `categoryWeights` from live.ts on the Map index (same arithmetic; parity-tested via live.ts). */
function teamWeights(
  byId: ReadonlyMap<string, DraftPlayer>,
  mine: readonly string[],
  punted: ReadonlySet<number>,
): number[] {
  const n = byId.values().next().value?.z.length ?? 0
  const lookup: Record<string, DraftPlayer> = {}
  for (const id of mine) lookup[id] = byId.get(id) as DraftPlayer
  if (mine.length === 0) return Array.from({ length: n }, (_, i) => (punted.has(i) ? 0 : 1))
  return categoryWeights(lookup, mine, punted)
}

function context(room: Room): Context {
  const { byId, sorted } = indexOf(room.players)
  const state = teamState(room.sales, room.teams, room.budget, room.slots)
  const taken = new Set(room.sales.map((x) => x.pid))
  const infl = fastInflation(sorted, taken, state)
  const weights: Record<string, number[]> = {}
  for (const t of room.teams) {
    const mine = room.sales.filter((x) => x.team === t).map((x) => x.pid)
    weights[t] = teamWeights(byId, mine, (room.managers[t] as Manager).punted)
  }
  let money = 0
  let open = 0
  for (const st of Object.values(state))
    if (st.open > 0) {
      money += st.left
      open += st.open
    }
  return { state, infl, byId, weights, taken, perSlot: open > 0 ? money / open : 0 }
}

function styleMultiplier(style: Style, usd: number): number {
  if (style === 'stars')
    return usd >= 35 ? TUNING.starsTop : usd <= 8 ? TUNING.starsLow : TUNING.starsMid
  if (style === 'value') return TUNING.valueHunter
  return 1
}

/** A simulated manager's walk-away price for a player: whole dollars, within its max bid (0 = can't buy). */
function walkAway(room: Room, ctx: Context, team: string, pid: string): number {
  const s = ctx.state[team] as TeamState
  if (s.open <= 0 || s.max_bid < 1) return 0
  const p = ctx.byId.get(pid) as DraftPlayer
  const m = room.managers[team] as Manager
  const adj = 1 + (p.usd - 1) * ctx.infl
  const fit = fitMultiplier(p.z, ctx.weights[team] as number[], m.punted)
  const noise = 1 + TUNING.noise * (2 * hash01(room.seed, 'v', team, pid) - 1)
  const v = Math.floor(adj * fit * styleMultiplier(m.style, p.usd) * noise * spendDown(ctx, s))
  return Math.max(1, Math.min(s.max_bid, v))
}

/** A manager with more cash per open spot than the room bids up (real rooms spend their money). */
function spendDown(ctx: Context, s: TeamState): number {
  const rich = ctx.perSlot > 0 ? s.left / s.open / ctx.perSlot : 1
  return rich > 1 ? Math.min(TUNING.richCap, 1 + TUNING.rich * (rich - 1)) : 1
}

/** Every simulated manager's walk-away price for one player (the human team is left out). */
export function walkAways(room: Room, pid: string): Record<string, number> {
  const ctx = context(room)
  const out: Record<string, number> = {}
  for (const t of room.teams)
    if (!(room.managers[t] as Manager).human) out[t] = walkAway(room, ctx, t, pid)
  return out
}

// --- nominations ---------------------------------------------------------------------------------

/** The team whose turn it is to nominate (rotating, skipping full rosters), or null when complete. */
export function nominator(room: Room): string | null {
  const state = teamState(room.sales, room.teams, room.budget, room.slots)
  for (let k = 0; k < room.teams.length; k++) {
    const t = room.teams[(room.turn + k) % room.teams.length] as string
    if ((state[t] as TeamState).open > 0) return t
  }
  return null
}

/** A simulated manager's nomination: usually its own top target, sometimes a budget drain. */
export function simNomination(room: Room, team: string): string {
  const ctx = context(room)
  const m = room.managers[team] as Manager
  const { sorted } = indexOf(room.players)
  const pool: { id: string; adj: number; fit: number }[] = []
  for (const p of sorted) {
    if (pool.length >= TUNING.pool) break
    if (ctx.taken.has(p.id)) continue
    pool.push({
      id: p.id,
      adj: 1 + (p.usd - 1) * ctx.infl,
      fit: fitMultiplier(p.z, ctx.weights[team] as number[], m.punted),
    })
  }
  const best = (f: (r: { adj: number; fit: number }) => number, rows: typeof pool) =>
    rows.reduce<(typeof pool)[number] | null>((a, r) => (a === null || f(r) > f(a) ? r : a), null)
  const drain = hash01(room.seed, 'drain', room.sales.length, team) < TUNING.drainShare
  const drains = pool.filter((r) => r.fit < 0.95)
  if (drain && drains.length > 0)
    return (best((r) => r.adj * (1 - r.fit), drains) as (typeof pool)[number]).id
  const pick = best((r) => r.adj * r.fit, pool)
  if (!pick)
    throw new Error('no players left to nominate: the room needs at least teams × slots players')
  return pick.id
}

// --- bidding -------------------------------------------------------------------------------------

/**
 * The next rival bid on a lot: the simulated manager (not the current high bidder, not the owner) with the
 * highest walk-away above the price bids price + 1. Null when nobody will go higher.
 */
export function rivalBid(
  room: Room,
  pid: string,
  price: number,
  high: string | null,
): { team: string; price: number } | null {
  const w = walkAways(room, pid)
  let best: string | null = null
  for (const t of room.teams) {
    if (t === high || !(t in w)) continue
    const v = w[t] as number
    if (
      v > price &&
      (best === null ||
        v > (w[best] as number) ||
        (v === w[best] && hash01(room.seed, 'tie', pid, t) > hash01(room.seed, 'tie', pid, best)))
    )
      best = t
  }
  return best ? { team: best, price: price + 1 } : null
}

/**
 * Settles a lot among simulated managers only (an English auction): the highest walk-away wins at the
 * second-highest + $1 (never above its own walk-away). The nominator opens at $1.
 */
export function settleSimLot(room: Room, pid: string, nominatedBy: string): Sale {
  const w = walkAways(room, pid)
  const bidders = Object.entries(w)
    .filter(([, v]) => v >= 1)
    .sort(
      (a, b) =>
        b[1] - a[1] || hash01(room.seed, 'tie', pid, b[0]) - hash01(room.seed, 'tie', pid, a[0]),
    )
  const [first, second] = bidders
  if (!first) return { pid, team: nominatedBy, price: 1 }
  const price = second ? Math.min(first[1], second[1] + 1) : 1
  return { pid, team: first[0], price: Math.max(1, price) }
}

/** Records a sale and passes the nomination to the next team. */
export function recordSale(room: Room, sale: Sale): Room {
  return {
    ...room,
    sales: [...room.sales, sale],
    turn: (room.teams.indexOf(nominator(room) ?? room.teams[0] ?? '') + 1) % room.teams.length,
  }
}

/** Runs simulated lots until the owner's nomination (when `untilMine`) or the end. */
export function simulate(room: Room, untilMine = false): Room {
  let r = room
  for (;;) {
    const nom = nominator(r)
    if (nom === null) return r
    if (untilMine && nom === r.me) return r
    if (nom === r.me) {
      // "Sim the rest": the owner's nomination and bids follow the helper's targets.
      const pid = simNomination(r, nom)
      r = recordSale(r, settleWithOwnerAuto(r, pid))
      continue
    }
    const pid = simNomination(r, nom)
    r = recordSale(r, r.me ? settleWithOwnerAuto(r, pid) : settleSimLot(r, pid, nom))
  }
}

/**
 * When the owner is auto-piloted, they bid up to the helper's ceiling, raised by the same spend-down
 * factor as the rivals (DRAFT-015: without it the owner finished with $45–88 unspent on real values).
 */
function settleWithOwnerAuto(room: Room, pid: string): Sale {
  const sim = settleSimLot(room, pid, room.me ?? '')
  if (!room.me) return sim
  const a = advise(
    room.players,
    room.sales,
    room.teams,
    room.me,
    room.budget,
    room.slots,
    (room.managers[room.me] as Manager).punted,
  )
  const state = a.teams[room.me] as TeamState
  const helper = a.players[pid]?.ceiling ?? 0
  const mine = Math.min(state.max_bid, Math.floor(helper * spendDown(context(room), state)))
  if (state.open <= 0 || mine < 1) return sim
  const rivals = walkAways(room, pid)
  const bestRival = Math.max(0, ...Object.values(rivals))
  if (mine > bestRival)
    return { pid, team: room.me, price: Math.max(1, Math.min(mine, bestRival + 1)) }
  return sim
}
