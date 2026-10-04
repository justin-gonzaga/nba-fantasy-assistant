import type { DraftPlayer, Sale } from './live'
import { addToHistory, buildReport, loadHistory } from './report'

// A hand-built 4-team room (16-team maths, smaller): "me" plus three rivals, 2 players each.
// Category strengths (9) are zero except PTS (0) and FT% (7) so ranks are easy to check.
const z = (pts: number, ft: number) => [pts, 0, 0, 0, 0, 0, 0, ft, 0]
const players: DraftPlayer[] = [
  { id: 'a', usd: 60, z: z(3, -2) },
  { id: 'b', usd: 10, z: z(1, -1) },
  { id: 'c', usd: 40, z: z(2, 1) },
  { id: 'd', usd: 5, z: z(0, 1) },
  { id: 'e', usd: 30, z: z(1, 2) },
  { id: 'f', usd: 8, z: z(0, 0) },
  { id: 'g', usd: 20, z: z(-1, 3) },
  { id: 'h', usd: 2, z: z(0, 0) },
]
const teams = ['me', 'r1', 'r2', 'r3']
const sales: Sale[] = [
  { pid: 'a', team: 'me', price: 70 },
  { pid: 'c', team: 'r1', price: 35 },
  { pid: 'e', team: 'r2', price: 30 },
  { pid: 'g', team: 'r3', price: 25 },
  { pid: 'b', team: 'me', price: 5 },
  { pid: 'd', team: 'r1', price: 4 },
  { pid: 'f', team: 'r2', price: 8 },
  { pid: 'h', team: 'r3', price: 1 },
]

describe('practice-draft report (DRAFT-015 AC1)', () => {
  const r = buildReport(players, sales, teams, 'me', null, 200, (pid) => pid.toUpperCase())

  it('totals spend, value and surplus', () => {
    expect(r.spent).toBe(75)
    expect(r.value).toBe(70)
    expect(r.surplus).toBe(-5)
    expect(r.left).toBe(125)
    expect(r.bestBuys).toEqual([{ pid: 'b', price: 5, value: 10, diff: 5 }])
    expect(r.overpays).toEqual([{ pid: 'a', price: 70, value: 60, diff: -10 }])
  })

  it('ranks each category against the room', () => {
    // PTS totals: me 4, r1 2, r2 1, r3 -1 → 1st; FT% totals: me -3, r1 2, r2 2, r3 3 → 4th
    expect(r.categories.find((c) => c.label === 'PTS')?.rank).toBe(1)
    expect(r.categories.find((c) => c.label === 'FT%')?.rank).toBe(4)
    // the 7 zero categories tie everyone: rank 1, nobody beaten
    expect(r.categories.find((c) => c.label === 'REB')?.rank).toBe(1)
  })

  it('counts projected category wins as the share of rivals beaten', () => {
    // PTS beats 3 of 3 = 1; FT% beats 0; the rest tie = 0 → 1.0
    expect(r.categoryWins).toBe(1)
  })

  it('tracks budget pace against the room', () => {
    // all 8 sales are within the first 50: me $75, room average (178 / 4) = $45 (rounded)
    expect(r.pace[0]).toEqual({ sale: 50, mine: 75, room: 45 })
  })
})

describe('lessons (DRAFT-015 AC2)', () => {
  it('are rule-based on the numbers', () => {
    const r = buildReport(players, sales, teams, 'me', null, 200, (pid) => pid.toUpperCase())
    // 70 + 5 = 37.5 % of the budget: under the 40 % rule, so no concentration lesson
    expect(r.lessons.some((l) => l.includes('% of your budget'))).toBe(false)
    expect(r.lessons).toContain(
      "You spent early: by sale 100 you had spent $75, the room's average team $45.",
    )
    expect(r.lessons.some((l) => l.startsWith('You finished with $125 unspent'))).toBe(true)
    const heavy = sales.map((s) => (s.pid === 'a' ? { ...s, price: 80 } : s))
    const h = buildReport(players, heavy, teams, 'me', null, 200, (pid) => pid.toUpperCase())
    expect(h.lessons[0]).toBe('You spent 43 % of your budget on 2 players (A and B).')
    expect(h.lessons.length).toBeLessThanOrEqual(3)
  })

  it('a punted category is intentional, not a weakness', () => {
    const punt = buildReport(players, sales, teams, 'me', 7, 200)
    expect(punt.categories.find((c) => c.label === 'FT%')).toMatchObject({ rank: 4, punted: true })
    expect(punt.lessons.some((l) => l.includes('FT%'))).toBe(false)
    const plain = buildReport(players, sales, teams, 'me', null, 200)
    // with only 4 teams FT% 4th isn't ≥ 13th, so no weakness lesson either way; check the 16-team rule:
    expect(plain.lessons.some((l) => l.includes('FT%'))).toBe(false)
  })

  it('flags the weakest non-punted category in a 16-team room', () => {
    const many = Array.from({ length: 15 }, (_, i) => `r${i + 1}`)
    const room = ['me', ...many]
    const extra: DraftPlayer[] = many.map((_, i) => ({ id: `x${i}`, usd: 1, z: z(0, 1) }))
    const s2: Sale[] = [
      { pid: 'a', team: 'me', price: 60 },
      ...many.map((t, i) => ({ pid: `x${i}`, team: t, price: 1 })),
    ]
    const r = buildReport([...players, ...extra], s2, room, 'me', null, 200)
    expect(r.categories.find((c) => c.label === 'FT%')?.rank).toBe(16)
    expect(r.lessons).toContain(
      'Your FT% ranks 16th of 16: 1 of your 5 most expensive players are below average in it.',
    )
  })
})

describe('history', () => {
  beforeEach(() => localStorage.clear())
  it('keeps the last 10 runs, newest first', () => {
    for (let i = 0; i < 12; i++)
      addToHistory({
        id: `run-${i}`,
        at: `2026-10-0${i % 9}`,
        seed: i,
        strategy: 'All categories',
        surplus: i,
        categoryWins: 4,
      })
    const h = loadHistory()
    expect(h).toHaveLength(10)
    expect(h[0]?.seed).toBe(11)
  })

  it('records a run once even if asked twice (React StrictMode)', () => {
    const run = {
      id: 'x',
      at: '2026-10-03',
      seed: 1,
      strategy: 'All categories',
      surplus: 0,
      categoryWins: 4,
    }
    addToHistory(run)
    addToHistory(run)
    expect(loadHistory()).toHaveLength(1)
  })
})
