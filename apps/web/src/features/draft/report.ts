// DRAFT-015: the practice-draft report. Pure: every number and lesson comes from the finished room.
import { CATEGORIES } from '../players/format'
import type { DraftPlayer, Sale } from './live'

export const PACE_MARKS = [50, 100, 150] as const

export type CategoryResult = { key: string; label: string; rank: number; punted: boolean }
export type Buy = { pid: string; price: number; value: number; diff: number }

export type Report = {
  spent: number
  value: number
  surplus: number
  left: number
  bestBuys: Buy[]
  overpays: Buy[]
  categories: CategoryResult[]
  /** Σ over non-punted categories of the share of the 15 rivals beaten (season projections). */
  categoryWins: number
  /** The owner's cumulative spend vs the room's average team after sales 50 / 100 / 150. */
  pace: { sale: number; mine: number; room: number }[]
  lessons: string[]
}

const ordinal = (n: number) => {
  const t = n % 100
  if (t >= 11 && t <= 13) return `${n}th`
  return `${n}${['th', 'st', 'nd', 'rd'][n % 10] ?? 'th'}`
}

export function buildReport(
  players: readonly DraftPlayer[],
  sales: readonly Sale[],
  teams: readonly string[],
  me: string,
  punted: number | null,
  budget = 200,
  names: (pid: string) => string = (pid) => pid,
): Report {
  const byId = new Map(players.map((p) => [p.id, p]))
  const mine = sales.filter((s) => s.team === me)
  const buys: Buy[] = mine.map((s) => {
    const value = Math.round(byId.get(s.pid)?.usd ?? 0)
    return { pid: s.pid, price: s.price, value, diff: value - s.price }
  })
  const spent = mine.reduce((a, s) => a + s.price, 0)
  const value = buys.reduce((a, b) => a + b.value, 0)

  // Category strength totals per team, then my rank (1 = best) in each category.
  const totals = new Map<string, number[]>()
  for (const t of teams)
    totals.set(
      t,
      CATEGORIES.map(() => 0),
    )
  for (const s of sales) {
    const z = byId.get(s.pid)?.z ?? []
    const row = totals.get(s.team)
    if (row) z.forEach((v, i) => (row[i] = (row[i] ?? 0) + v))
  }
  const myTotals = totals.get(me) ?? []
  const rivals = teams.filter((t) => t !== me)
  let categoryWins = 0
  const categories: CategoryResult[] = CATEGORIES.map(([key, label], i) => {
    const m = myTotals[i] ?? 0
    const beaten = rivals.filter((t) => (totals.get(t)?.[i] ?? 0) < m).length
    const better = rivals.filter((t) => (totals.get(t)?.[i] ?? 0) > m).length
    const isPunt = punted === i
    if (!isPunt) categoryWins += beaten / rivals.length
    return { key, label, rank: better + 1, punted: isPunt }
  })

  const pace = PACE_MARKS.map((sale) => {
    const upTo = sales.slice(0, sale)
    const mineUpTo = upTo.filter((s) => s.team === me).reduce((a, s) => a + s.price, 0)
    const all = upTo.reduce((a, s) => a + s.price, 0)
    return { sale, mine: mineUpTo, room: Math.round(all / teams.length) }
  })

  const sortedBuys = [...buys].sort((a, b) => b.diff - a.diff)
  const report: Report = {
    spent,
    value,
    surplus: value - spent,
    left: budget - spent,
    bestBuys: sortedBuys.filter((b) => b.diff > 0).slice(0, 3),
    overpays: [...sortedBuys]
      .reverse()
      .filter((b) => b.diff < 0)
      .slice(0, 3),
    categories,
    categoryWins: Math.round(categoryWins * 10) / 10,
    pace,
    lessons: [],
  }
  report.lessons = lessons(report, mine, byId, names)
  return report
}

/** Up to three rule-based lessons, most important first. Each is built only from the report's numbers. */
function lessons(
  r: Report,
  mine: readonly Sale[],
  byId: Map<string, DraftPlayer>,
  names: (pid: string) => string,
): string[] {
  const out: string[] = []
  const top2 = [...mine].sort((a, b) => b.price - a.price).slice(0, 2)
  const top2Share = r.spent > 0 ? top2.reduce((a, s) => a + s.price, 0) / (r.spent + r.left) : 0
  if (top2.length === 2 && top2Share >= 0.4)
    out.push(
      `You spent ${Math.round(top2Share * 100)} % of your budget on 2 players (${top2.map((s) => names(s.pid)).join(' and ')}).`,
    )

  const weak = r.categories
    .filter((c) => !c.punted && c.rank >= 13)
    .sort((a, b) => b.rank - a.rank)[0]
  if (weak) {
    const i = r.categories.findIndex((c) => c.key === weak.key)
    const topFive = [...mine].sort((a, b) => b.price - a.price).slice(0, 5)
    const below = topFive.filter((s) => (byId.get(s.pid)?.z[i] ?? 0) < 0).length
    out.push(
      `Your ${weak.label} ranks ${ordinal(weak.rank)} of 16: ${below} of your 5 most expensive players are below average in it.`,
    )
  }

  const mid = r.pace.find((p) => p.sale === 100)
  if (mid && mid.room > 0) {
    if (mid.mine < 0.7 * mid.room)
      out.push(
        `You waited: by sale 100 you had spent $${mid.mine}, the room's average team $${mid.room}.`,
      )
    else if (mid.mine > 1.3 * mid.room)
      out.push(
        `You spent early: by sale 100 you had spent $${mid.mine}, the room's average team $${mid.room}.`,
      )
  }

  if (r.left >= 10) out.push(`You finished with $${r.left} unspent: money left is value lost.`)
  if (r.surplus >= 15) out.push(`Good value: your team is worth $${r.surplus} more than you paid.`)
  else if (r.surplus <= -15)
    out.push(`You paid $${-r.surplus} more than your team's published value.`)

  return out.slice(0, 3)
}

// --- history -------------------------------------------------------------------------------------

export const HISTORY_KEY = 'draft-practice-history-v1'
export type RunSummary = {
  /** One per practice run (seed + start time), so a run is recorded once. */
  id: string
  at: string
  seed: number
  strategy: string
  surplus: number
  categoryWins: number
}

export function loadHistory(): RunSummary[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? (JSON.parse(raw) as RunSummary[]) : []
  } catch {
    return []
  }
}

export function addToHistory(run: RunSummary): RunSummary[] {
  const past = loadHistory()
  // React StrictMode runs state initialisers twice in development: never record a run twice.
  if (past.some((r) => r.id === run.id)) return past
  const next = [run, ...past].slice(0, 10)
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
  } catch {
    // storage blocked: the report still shows, there's just no history
  }
  return next
}
