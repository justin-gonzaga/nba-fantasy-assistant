// SIM-003: one week of a replayed season under this league's rules (Yahoo H2H, 9 categories), scored on
// the players' real game lines. Pure: every function returns new state; nothing reads the clock.
//
// Rules (league settings + G-31): starters G G G F F F C Util Util Util (bench the rest); lineups are
// daily, auto by default (the most valuable eligible players with a game start); at most 4 acquisitions
// a week, each playing from the day after it is made; rivals auto-start and make no moves.
// "Most valuable" uses pre-season value only, never what a player went on to score that day.

export type ReplayPlayer = {
  id: number
  name: string
  team: string | null
  pos: string | null
  usd: number
  rank: number | null
  z: number[]
}

export type Line = {
  pts: number
  reb: number
  ast: number
  stl: number
  blk: number
  fg3m: number
  tov: number
  fgm: number
  fga: number
  ftm: number
  fta: number
}

export const SLOTS = ['G', 'G', 'G', 'F', 'F', 'F', 'C', 'Util', 'Util', 'Util'] as const
export type Slot = (typeof SLOTS)[number]
export const MAX_ADDS = 4

/** Whether a player with NBA position(s) like "G-F" can fill a slot; an unknown position fills Util only. */
export function eligible(pos: string | null, slot: Slot): boolean {
  if (slot === 'Util') return true
  if (!pos) return false
  return pos.split('-').includes(slot)
}

/**
 * The day's starters: players with a game, not benched, placed into slots to maximise how many (and
 * which, by pre-season value) start. Greedy by value with augmenting paths (a transversal-matroid greedy,
 * which is optimal), so a G-F never strands a third guard.
 */
export function autoLineup(
  roster: readonly number[],
  playing: ReadonlySet<number>,
  players: ReadonlyMap<number, ReplayPlayer>,
  benched: ReadonlySet<number>,
): Map<number, number> {
  const candidates = roster
    .filter((id) => playing.has(id) && !benched.has(id))
    .sort((a, b) => (players.get(b)?.usd ?? 0) - (players.get(a)?.usd ?? 0) || a - b)
  const slotOf = new Map<number, number>() // player → slot index
  const holder = new Array<number | null>(SLOTS.length).fill(null)

  const place = (id: number, seen: Set<number>): boolean => {
    const pos = players.get(id)?.pos ?? null
    for (let s = 0; s < SLOTS.length; s++) {
      if (!eligible(pos, SLOTS[s] as Slot) || seen.has(s)) continue
      seen.add(s)
      const current = holder[s]
      if (current === null || current === undefined || place(current, seen)) {
        holder[s] = id
        slotOf.set(id, s)
        return true
      }
    }
    return false
  }
  for (const id of candidates) place(id, new Set())
  return slotOf
}

export type Move = { madeOn: number; add: number; drop: number } // madeOn: day index, −1 = before the week

export type WeekState = {
  days: readonly string[] // ISO dates, Monday … Sunday
  mine: readonly number[] // my roster at the start of the week
  theirs: readonly number[]
  /** Everyone on any roster in the league at the start of the week (free agents are the rest). */
  taken: ReadonlySet<number>
  moves: readonly Move[]
  /** day index → players I benched that day */
  benched: ReadonlyMap<number, ReadonlySet<number>>
}

/** My roster on a given day, with the moves that have taken effect (a move plays from the next day). */
export function rosterOn(state: WeekState, day: number): number[] {
  let roster = [...state.mine]
  for (const m of state.moves) {
    if (m.madeOn + 1 <= day) roster = roster.filter((id) => id !== m.drop).concat(m.add)
  }
  return roster
}

/** Everyone I hold or have added (for free-agent checks): the latest roster plus pending adds. */
function rosterAfterMoves(state: WeekState): number[] {
  let roster = [...state.mine]
  for (const m of state.moves) roster = roster.filter((id) => id !== m.drop).concat(m.add)
  return roster
}

export type MoveResult = { state: WeekState; error: string | null }

export function addPlayer(state: WeekState, madeOn: number, add: number, drop: number): MoveResult {
  const fail = (error: string) => ({ state, error })
  if (state.moves.length >= MAX_ADDS) return fail(`You've used all ${MAX_ADDS} adds this week.`)
  const mine = rosterAfterMoves(state)
  const dropped = new Set(state.moves.map((m) => m.drop))
  const free = (!state.taken.has(add) || dropped.has(add)) && !mine.includes(add)
  if (!free || state.theirs.includes(add)) return fail('That player is not a free agent.')
  if (!mine.includes(drop)) return fail('That player is not on your roster.')
  if (madeOn < -1 || madeOn >= state.days.length - 1)
    return fail('That move would start after the week ends.')
  return { state: { ...state, moves: [...state.moves, { madeOn, add, drop }] }, error: null }
}

export const CATEGORIES = [
  ['pts', 'PTS'],
  ['reb', 'REB'],
  ['ast', 'AST'],
  ['stl', 'STL'],
  ['blk', 'BLK'],
  ['fg3m', '3PM'],
  ['fg_pct', 'FG%'],
  ['ft_pct', 'FT%'],
  ['tov', 'TO'],
] as const

export type CategoryResult = {
  key: string
  label: string
  mine: number
  theirs: number
  result: 'win' | 'loss' | 'tie'
}

export type DayStarters = { day: string; mine: number[]; theirs: number[] }

export type WeekResult = {
  categories: CategoryResult[]
  record: { wins: number; losses: number; ties: number }
  days: DayStarters[]
}

const COUNTING = [
  'pts',
  'reb',
  'ast',
  'stl',
  'blk',
  'fg3m',
  'tov',
  'fgm',
  'fga',
  'ftm',
  'fta',
] as const

function emptyTotals(): Record<(typeof COUNTING)[number], number> {
  return { pts: 0, reb: 0, ast: 0, stl: 0, blk: 0, fg3m: 0, tov: 0, fgm: 0, fga: 0, ftm: 0, fta: 0 }
}

/** Plays the week: each day both sides' starters score their real lines; then the 9 categories. */
export function playWeek(
  state: WeekState,
  players: ReadonlyMap<number, ReplayPlayer>,
  lines: ReadonlyMap<string, ReadonlyMap<number, Line>>,
  /** SIM-004: who has a game each day, from the schedule. Without it, a game = a line (tests). With it, a
   *  scheduled starter who sat out still takes his slot and scores 0, as in Yahoo. */
  hasGame?: (pid: number, date: string) => boolean,
): WeekResult {
  const mineTot = emptyTotals()
  const theirTot = emptyTotals()
  const days: DayStarters[] = []
  state.days.forEach((day, i) => {
    const today = lines.get(day) ?? new Map<number, Line>()
    const mineToday = rosterOn(state, i)
    const playing = hasGame
      ? new Set([...mineToday, ...state.theirs].filter((pid) => hasGame(pid, day)))
      : new Set(today.keys())
    const mine = [
      ...autoLineup(mineToday, playing, players, state.benched.get(i) ?? new Set()).keys(),
    ]
    const theirs = [...autoLineup(state.theirs, playing, players, new Set()).keys()]
    for (const [ids, tot] of [
      [mine, mineTot],
      [theirs, theirTot],
    ] as const) {
      for (const id of ids) {
        const l = today.get(id)
        if (l) for (const k of COUNTING) tot[k] += l[k]
      }
    }
    days.push({ day, mine, theirs })
  })
  const value = (t: ReturnType<typeof emptyTotals>, key: string): number => {
    if (key === 'fg_pct') return t.fga > 0 ? t.fgm / t.fga : 0
    if (key === 'ft_pct') return t.fta > 0 ? t.ftm / t.fta : 0
    return t[key as (typeof COUNTING)[number]]
  }
  const categories: CategoryResult[] = CATEGORIES.map(([key, label]) => {
    const mine = value(mineTot, key)
    const theirs = value(theirTot, key)
    const lowerWins = key === 'tov'
    const result = mine === theirs ? 'tie' : mine > theirs !== lowerWins ? 'win' : 'loss'
    return { key, label, mine, theirs, result }
  })
  const count = (r: CategoryResult['result']) => categories.filter((c) => c.result === r).length
  return {
    categories,
    record: { wins: count('win'), losses: count('loss'), ties: count('tie') },
    days,
  }
}
