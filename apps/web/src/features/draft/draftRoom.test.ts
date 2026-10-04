import parity from './fixtures/advise-parity.json'
import values from './fixtures/values-2026-27.json'
import { advise, teamState, type DraftPlayer, type Sale } from './live'
import { createRoom, simulate, type Room } from './room'

const TEAMS = Array.from({ length: 16 }, (_, i) => `T${i + 1}`)
const players = values.players as DraftPlayer[]
const SEEDS = Array.from({ length: 50 }, (_, i) => i + 1)

/** Replays a finished room sale by sale, checking each price against the buyer's max bid at that moment. */
function overMaxBid(room: Room): Sale[] {
  const bad: Sale[] = []
  room.sales.forEach((sale, i) => {
    const before = teamState(room.sales.slice(0, i), room.teams, room.budget, room.slots)
    if (sale.price > (before[sale.team]?.max_bid ?? 0) || sale.price < 1) bad.push(sale)
  })
  return bad
}

const rooms = new Map<number, Room>()
const roomFor = (seed: number) => {
  let r = rooms.get(seed)
  if (!r) {
    r = simulate(createRoom({ players, teams: TEAMS, me: null, seed }))
    rooms.set(seed, r)
  }
  return r
}

describe('parity with draft_live (DRAFT-013 AC3)', () => {
  it('matches the Python engine on the shared fixture', () => {
    const c = parity.case
    const e = parity.expected
    const a = advise(c.players, c.picks, c.teams, c.me, c.budget, c.slots, new Set(c.punted))
    expect(a.inflation).toBeCloseTo(e.inflation, 9)
    a.weights.forEach((w, i) => expect(w).toBeCloseTo(e.weights[i] as number, 9))
    expect(a.my_max_bid).toBe(e.my_max_bid)
    expect(a.targets).toEqual(e.targets)
    expect(a.hints).toEqual(e.hints)
    const exp = e.players as Record<string, { adj: number; fit: number; ceiling: number }>
    expect(Object.keys(a.players).sort()).toEqual(Object.keys(exp).sort())
    for (const [pid, r] of Object.entries(exp)) {
      expect(a.players[pid]?.adj).toBeCloseTo(r.adj, 9)
      expect(a.players[pid]?.fit).toBeCloseTo(r.fit, 9)
      expect(a.players[pid]?.ceiling).toBe(r.ceiling)
    }
    for (const [t, s] of Object.entries(
      e.teams as Record<string, { left: number; open: number; max_bid: number }>,
    )) {
      expect(a.teams[t]).toMatchObject(s)
    }
  })
})

describe('the simulated room (DRAFT-013 AC1)', () => {
  it('always completes: 224 sales, 14 players and ≤ $200 per team, no bid over a max bid', () => {
    for (const seed of SEEDS) {
      const room = roomFor(seed)
      expect(room.sales, `seed ${seed}`).toHaveLength(224)
      const final = teamState(room.sales, room.teams, room.budget, room.slots)
      for (const s of Object.values(final)) {
        expect(s.count).toBe(14)
        expect(s.spent).toBeLessThanOrEqual(200)
      }
      expect(new Set(room.sales.map((s) => s.pid)).size).toBe(224)
      expect(overMaxBid(room), `seed ${seed}`).toEqual([])
    }
  }, 120_000)

  it('also completes with an auto-piloted owner ("sim the rest")', () => {
    const room = simulate(createRoom({ players, teams: TEAMS, me: 'T1', seed: 7 }))
    expect(room.sales).toHaveLength(224)
    expect(room.sales.filter((s) => s.team === 'T1')).toHaveLength(14)
    expect(overMaxBid(room)).toEqual([])
  }, 60_000)
})

describe('auto-piloted owner (DRAFT-015)', () => {
  it('spends its money like the rivals do: ≥ 95 % of the budget across 20 rooms', () => {
    const lefts = Array.from({ length: 20 }, (_, i) => {
      const room = simulate(createRoom({ players, teams: TEAMS, me: 'T1', seed: 100 + i }))
      return teamState(room.sales, room.teams, room.budget, room.slots).T1?.left ?? 200
    })
    process.stdout.write(`
owner left: ${lefts.join(',')}
`)
    for (const left of lefts) expect(left).toBeLessThanOrEqual(10)
  }, 120_000)
})

describe('calibration (DRAFT-013 AC2)', () => {
  it('prices the top 50 within ±15 % of the published values and spends ≥ 97 % of the money', () => {
    const top50 = [...players].sort((a, b) => b.usd - a.usd).slice(0, 50)
    const usd = new Map(top50.map((p) => [p.id, p.usd]))
    let paid = 0
    let worth = 0
    const spends: number[] = []
    for (const seed of SEEDS) {
      const room = roomFor(seed)
      for (const s of room.sales) {
        const u = usd.get(s.pid)
        if (u !== undefined) {
          paid += s.price
          worth += u
        }
      }
      spends.push(room.sales.reduce((a, s) => a + s.price, 0))
    }
    const ratio = paid / worth
    // Evidence: printed so the task file can record the calibration.
    process.stdout.write(
      `
calibration: top-50 price/value ${ratio.toFixed(3)}; spend min ${Math.min(...spends)} mean ${(spends.reduce((a, b) => a + b, 0) / spends.length).toFixed(0)} of 3200
`,
    )
    expect(ratio).toBeGreaterThanOrEqual(0.85)
    expect(ratio).toBeLessThanOrEqual(1.15)
    for (const s of spends) expect(s).toBeGreaterThanOrEqual(0.97 * 3200)
  }, 120_000)
})

describe('seeded replay (DRAFT-013 AC4)', () => {
  it('the same seed replays the same room; another seed does not', () => {
    const a = simulate(createRoom({ players, teams: TEAMS, me: null, seed: 3 }))
    const b = simulate(createRoom({ players, teams: TEAMS, me: null, seed: 3 }))
    const c = simulate(createRoom({ players, teams: TEAMS, me: null, seed: 4 }))
    expect(a.sales).toEqual(b.sales)
    expect(a.sales).not.toEqual(c.sales)
  }, 60_000)
})
