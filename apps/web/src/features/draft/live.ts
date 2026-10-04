// DRAFT-013: the live auction helper in TypeScript, a line-for-line port of
// fantasy_models/draft_live.py (and the board's draft_live.js). Parity: fixtures/advise-parity.json,
// owned by apps/pipeline/tests/test_draft_room_parity_fixture.py.

export type DraftPlayer = { id: string; usd: number; z: number[] }
export type Sale = { pid: string; team: string; price: number }
export type TeamState = {
  spent: number
  count: number
  left: number
  open: number
  max_bid: number
}
export type PlayerAdvice = { id: string; adj: number; fit: number; ceiling: number }
export type Advice = {
  inflation: number
  weights: number[]
  my_max_bid: number
  teams: Record<string, TeamState>
  players: Record<string, PlayerAdvice>
  targets: string[]
  hints: string[]
}

const FIT_CAP = 0.25
const FIT_ALPHA = 0.5
const W_LO = 0.5
const W_HI = 1.5
const HINT_POOL = 60
const HINT_FIT_BELOW = 0.95

const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x))

export function teamState(
  picks: readonly Sale[],
  teams: readonly string[],
  budget: number,
  slots: number,
): Record<string, TeamState> {
  const out: Record<string, TeamState> = {}
  for (const t of teams) out[t] = { spent: 0, count: 0, left: 0, open: 0, max_bid: 0 }
  for (const p of picks) {
    const s = out[p.team] as TeamState
    s.spent += p.price
    s.count += 1
  }
  for (const t of teams) {
    const s = out[t] as TeamState
    s.left = budget - s.spent
    s.open = slots - s.count
    s.max_bid = s.open > 0 ? Math.max(0, s.left - Math.max(0, s.open - 1)) : 0
  }
  return out
}

/** Money chasing the remaining value: only teams that can still buy count (a full roster's cash is dead). */
export function inflation(
  players: readonly DraftPlayer[],
  taken: ReadonlySet<string>,
  state: Record<string, TeamState>,
): number {
  let money = 0
  let open = 0
  for (const s of Object.values(state)) {
    if (s.open > 0) money += s.left
    open += s.open
  }
  const left = players
    .filter((p) => !taken.has(p.id))
    .map((p) => p.usd)
    .sort((a, b) => b - a)
    .slice(0, open)
  const above = left.reduce((a, u) => a + Math.max(0, u - 1), 0)
  if (open <= 0 || above <= 0) return 1
  return Math.max(0, money - open) / above
}

export function categoryWeights(
  byId: Record<string, DraftPlayer>,
  mine: readonly string[],
  punted: ReadonlySet<number>,
): number[] {
  const first = Object.values(byId)[0]
  const n = first ? first.z.length : 0
  const w: number[] = []
  for (let i = 0; i < n; i++) {
    if (punted.has(i)) {
      w.push(0)
      continue
    }
    if (mine.length === 0) {
      w.push(1)
      continue
    }
    let s = 0
    for (const id of mine) s += (byId[id] as DraftPlayer).z[i] as number
    w.push(clamp(1 - FIT_ALPHA * (s / mine.length), W_LO, W_HI))
  }
  return w
}

export function fitMultiplier(
  z: readonly number[],
  weights: readonly number[],
  punted: ReadonlySet<number>,
): number {
  let base = 0
  let fit = 0
  for (let i = 0; i < z.length; i++) {
    if (!punted.has(i)) base += z[i] as number
    fit += (weights[i] as number) * (z[i] as number)
  }
  if (base <= 0) return 1
  return clamp(fit / base, 1 - FIT_CAP, 1 + FIT_CAP)
}

const byKey =
  <T extends { id: string }>(f: (r: T) => number) =>
  (a: T, b: T) =>
    f(a) - f(b) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)

/** Everything the board shows after a sale: my max bid, per-player ceilings, targets, nomination hints. */
export function advise(
  players: readonly DraftPlayer[],
  picks: readonly Sale[],
  teams: readonly string[],
  me: string,
  budget: number,
  slots: number,
  punted: ReadonlySet<number> = new Set(),
): Advice {
  const byId: Record<string, DraftPlayer> = {}
  for (const p of players) byId[p.id] = p
  const taken = new Set(picks.map((p) => p.pid))
  const state = teamState(picks, teams, budget, slots)
  const infl = inflation(players, taken, state)
  const mine = picks.filter((p) => p.team === me).map((p) => p.pid)
  const weights = categoryWeights(byId, mine, punted)
  const myMax = (state[me] as TeamState).max_bid
  const rows: PlayerAdvice[] = []
  for (const p of players) {
    if (taken.has(p.id)) continue
    const adj = 1 + (p.usd - 1) * infl
    const fit = fitMultiplier(p.z, weights, punted)
    const ceiling = myMax >= 1 ? Math.trunc(Math.min(myMax, adj * fit)) : 0
    rows.push({ id: p.id, adj, fit, ceiling })
  }
  const targets = [...rows].sort(byKey((r) => -r.adj * r.fit)).slice(0, 10)
  const top = [...rows].sort(byKey((r) => -r.adj)).slice(0, HINT_POOL)
  const hints = top
    .filter((r) => r.fit < HINT_FIT_BELOW)
    .sort(byKey((r) => -r.adj * (1 - r.fit)))
    .slice(0, 5)
  const pmap: Record<string, PlayerAdvice> = {}
  for (const r of rows) pmap[r.id] = r
  return {
    inflation: infl,
    weights,
    my_max_bid: myMax,
    teams: state,
    players: pmap,
    targets: targets.map((r) => r.id),
    hints: hints.map((r) => r.id),
  }
}
