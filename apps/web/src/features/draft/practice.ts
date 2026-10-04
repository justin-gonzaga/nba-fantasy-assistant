// DRAFT-014: the practice draft as a pure state machine over the immutable Room (room.ts).
// The page drives it with owner actions and timer expiries; every transition returns a new state.
import type { PlayerRow } from '../../api/types'
import { CATEGORIES } from '../players/format'
import { advise, teamState, type Advice, type DraftPlayer, type Sale } from './live'
import {
  createRoom,
  nominator,
  recordSale,
  simNomination,
  simulate,
  walkAways,
  type Room,
  type Style,
} from './room'

export const ME = 'You'
export const TEAMS = [ME, ...Array.from({ length: 15 }, (_, i) => `Team ${i + 2}`)]
export const NOMINATE_SECONDS = 30
export const BID_SECONDS = 20

export type Pace = 'real' | 'untimed'
export type Settings = {
  seed: number
  styles: 'mix' | Style
  punted: number | null
  pace: Pace
  /** When this run started (ISO), with the seed it identifies the run in the history. */
  startedAt?: string
  /** SIM-002: a past season to replay (its pre-season values); absent = this season. */
  season?: string
}

export type Lot = {
  pid: string
  nominatedBy: string
  price: number
  high: string
  /** The rivals' walk-away prices for this player (fixed for the lot). */
  walk: Record<string, number>
  /** Whether the owner has bid in this lot (undo only goes back to lots the owner took part in). */
  ownerBid: boolean
}

export type Practice = {
  settings: Settings
  room: Room
  phase: 'nominate' | 'lot' | 'done'
  lot: Lot | null
  /** Rooms before each lot the owner nominated or bid in, newest last. */
  undo: Room[]
}

/** PlayerRows → the room's players: $ value and category strengths in the board's order. */
export function toDraftPlayers(rows: readonly PlayerRow[]): DraftPlayer[] {
  return rows.map((p) => ({
    id: String(p.id),
    usd: Math.max(0, p.dollars),
    z: CATEGORIES.map(([k]) => p.strengths[k] ?? 0),
  }))
}

const punts = (s: Settings) => (s.punted === null ? new Set<number>() : new Set([s.punted]))

export function myAdvice(p: Practice): Advice {
  const r = p.room
  return advise(r.players, r.sales, r.teams, ME, r.budget, r.slots, punts(p.settings))
}

export const myState = (p: Practice) =>
  teamState(p.room.sales, p.room.teams, p.room.budget, p.room.slots)[ME] as ReturnType<
    typeof teamState
  >[string]

// --- lots ----------------------------------------------------------------------------------------

/** Rivals bid among themselves ($1 steps) until nobody but the high bidder will go higher. */
function rivalsSettle(
  walk: Record<string, number>,
  order: readonly string[],
  price: number,
  high: string,
) {
  let p = price
  let h = high
  for (;;) {
    let best: string | null = null
    for (const t of order) {
      if (t === h) continue
      const w = walk[t] ?? 0
      if (w > p && (best === null || w > (walk[best] ?? 0))) best = t
    }
    if (best === null) return { price: p, high: h }
    p += 1
    h = best
  }
}

/** Opens a lot at $1 for the nominator; rivals bid it up to where only one rival remains. */
function openLot(p: Practice, pid: string, nominatedBy: string): Practice {
  const walk = walkAways(p.room, pid)
  const { price, high } = rivalsSettle(walk, p.room.teams, 1, nominatedBy)
  const lot: Lot = { pid, nominatedBy, price, high, walk, ownerBid: nominatedBy === ME }
  return { ...p, phase: 'lot', lot }
}

function canBid(p: Practice): boolean {
  const s = myState(p)
  return s.open > 0 && s.max_bid >= (p.lot ? p.lot.price + 1 : 1)
}

/**
 * Moves to the next decision for the owner: their nomination, or a lot they can still bid on. Lots the
 * owner can't take part in (full roster, not enough money) settle instantly among the rivals.
 */
export function nextDecision(p: Practice): Practice {
  let cur: Practice = { ...p, lot: null }
  for (;;) {
    const nom = nominator(cur.room)
    if (nom === null) return { ...cur, phase: 'done', lot: null }
    if (nom === ME) return { ...cur, phase: 'nominate' }
    const pid = simNomination(cur.room, nom)
    const opened = openLot(cur, pid, nom)
    if (canBid(opened)) return opened
    cur = sell({ ...opened, lot: opened.lot }, false)
  }
}

function sell(p: Practice, decide = true): Practice {
  const lot = p.lot as Lot
  const sale: Sale = { pid: lot.pid, team: lot.high, price: lot.price }
  const next: Practice = { ...p, room: recordSale(p.room, sale), lot: null }
  return decide ? nextDecision(next) : next
}

// --- owner actions -------------------------------------------------------------------------------

export function start(players: readonly DraftPlayer[], settings: Settings): Practice {
  const room = createRoom({
    players,
    teams: TEAMS,
    me: ME,
    seed: settings.seed,
    styles: settings.styles,
    myPunted: punts(settings),
  })
  return nextDecision({ settings, room, phase: 'nominate', lot: null, undo: [] })
}

export function nominate(p: Practice, pid: string): Practice {
  if (p.phase !== 'nominate' || p.room.sales.some((s) => s.pid === pid)) return p
  return { ...openLot({ ...p, undo: [...p.undo, p.room] }, pid, ME) }
}

export type BidResult = { practice: Practice; error: string | null }

/** The owner bids `amount`; the rivals answer at once. Errors explain why a bid isn't allowed. */
export function bid(p: Practice, amount: number): BidResult {
  const lot = p.lot
  if (p.phase !== 'lot' || !lot) return { practice: p, error: null }
  const s = myState(p)
  if (s.open <= 0) return { practice: p, error: 'Your roster is full.' }
  if (!Number.isInteger(amount) || amount <= lot.price)
    return { practice: p, error: `Bid more than $${lot.price}.` }
  if (amount > s.max_bid)
    return {
      practice: p,
      error: `Your max bid is $${s.max_bid}: you need $1 for each of your other ${s.open - 1} open spots.`,
    }
  const undo = lot.ownerBid ? p.undo : [...p.undo, p.room]
  const answered = rivalsSettle(lot.walk, p.room.teams, amount, ME)
  const next: Practice = { ...p, undo, lot: { ...lot, ...answered, ownerBid: true } }
  // Walk-aways are fixed for the lot: if no rival answered, nobody will, so it sells now.
  return { practice: answered.high === ME ? sell(next) : next, error: null }
}

/** The owner stops bidding (or the timer ran out): the lot goes to the high bidder. */
export const pass = (p: Practice): Practice => (p.phase === 'lot' && p.lot ? sell(p) : p)

/** The bid timer ran out: same as a pass (the high bidder wins, possibly the owner). */
export const bidExpired = pass

/** The nomination timer ran out: the helper's top target is nominated. */
export function nominateExpired(p: Practice): Practice {
  if (p.phase !== 'nominate') return p
  const top = myAdvice(p).targets[0]
  return top ? nominate(p, top) : p
}

/** Back to before the last lot the owner nominated or bid in. */
export function undoLast(p: Practice): Practice {
  const prev = p.undo[p.undo.length - 1]
  if (!prev) return p
  return nextDecision({ ...p, room: prev, undo: p.undo.slice(0, -1) })
}

/** Fast-forward: the owner bids up to the helper's ceilings until their next nomination, or to the end. */
export function fastForward(p: Practice, untilMine: boolean): Practice {
  const base = p.phase === 'lot' && p.lot ? sell(p, false) : p
  const room = simulate(base.room, untilMine)
  return nextDecision({ ...base, room })
}

// --- saving --------------------------------------------------------------------------------------

export const SAVE_KEY = 'draft-practice-v1'
type Saved = { settings: Settings; sales: Sale[]; turn: number }

export function save(p: Practice): void {
  try {
    const saved: Saved = { settings: p.settings, sales: p.room.sales, turn: p.room.turn }
    localStorage.setItem(SAVE_KEY, JSON.stringify(saved))
  } catch {
    // storage blocked: practice still works, it just won't resume
  }
}

export function clearSave(): void {
  try {
    localStorage.removeItem(SAVE_KEY)
  } catch {
    // nothing to clear
  }
}

export function loadSave(): Saved | null {
  try {
    const raw = localStorage.getItem(SAVE_KEY)
    return raw ? (JSON.parse(raw) as Saved) : null
  } catch {
    return null
  }
}

/** Rebuilds a saved practice on the current player list (unknown players drop out of the sales). */
export function resume(players: readonly DraftPlayer[], saved: Saved): Practice {
  const fresh = start(players, saved.settings)
  const known = new Set(players.map((x) => x.id))
  const sales = saved.sales.filter((s) => known.has(s.pid) && TEAMS.includes(s.team))
  return nextDecision({ ...fresh, room: { ...fresh.room, sales, turn: saved.turn }, undo: [] })
}

// --- glanceable advice (DRAFT-016) ---------------------------------------------------------------

type Cat = { key: string; label: string; weight: number }
const STRONG_Z = 0.5 // a player's "strong" categories: at least half a standard deviation above average

/** Your neediest categories (weight > 1, top 3) and best-covered ones (weight < 1, top 2), from the
 *  engine's live category weights; a punted category is neither. */
export function needs(weights: readonly number[], punted: number | null) {
  const cats: Cat[] = CATEGORIES.map(([key, label], i) => ({ key, label, weight: weights[i] ?? 1 }))
  const live = cats.filter((_, i) => i !== punted)
  return {
    need: live
      .filter((c) => c.weight > 1)
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 3),
    covered: live
      .filter((c) => c.weight < 1)
      .sort((a, b) => a.weight - b.weight)
      .slice(0, 2),
    punted: punted === null ? null : (CATEGORIES[punted]?.[1] ?? null),
  }
}

/** Why a player's ceiling moved: the needs he fills, or what he overlaps (fit from the engine). */
export function fitLine(
  z: readonly number[],
  weights: readonly number[],
  fit: number,
  punted: number | null = null,
): string {
  const strong = CATEGORIES.map(([, label], i) => ({ label, z: z[i] ?? 0, w: weights[i] ?? 1 }))
    .filter((c) => c.z >= STRONG_Z && c.w > 0)
    .sort((a, b) => b.z - a.z)
  // "Your needs" are exactly the categories the Needs panel lists (its top 3), so the two always agree.
  const listed = new Set(needs(weights, punted).need.map((c) => c.label))
  if (fit > 1.03) {
    const fills = strong.filter((c) => listed.has(c.label)).slice(0, 2)
    return fills.length
      ? `Fits your needs: ${fills.map((c) => c.label).join(', ')}`
      : 'Fits your build'
  }
  if (fit < 0.97) {
    const overlaps = strong.filter((c) => c.w < 1).slice(0, 2)
    return overlaps.length
      ? `Overlaps your team: ${overlaps.map((c) => c.label).join(', ')}`
      : 'Overlaps your team'
  }
  return 'Neutral fit'
}

export type Verdict = 'good' | 'near' | 'pass' | 'cant'

/** The bid state at a glance: the next bid against your ceiling (good ≤ 85 %, near ≤ 100 %). */
export function verdict(price: number, ceiling: number, canBid: boolean): Verdict {
  if (!canBid || ceiling < 1) return 'cant'
  const next = price + 1
  if (next <= 0.85 * ceiling) return 'good'
  if (next <= ceiling) return 'near'
  return 'pass'
}
