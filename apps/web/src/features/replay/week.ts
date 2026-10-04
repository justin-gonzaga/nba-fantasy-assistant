// SIM-004: one week of a saved replay league, as the page plays it. Pure: the page holds the state.

import type { ReplayLeague, WeekRecord } from './league'
import { rosterOn, type ReplayPlayer, type WeekResult, type WeekState } from './matchup'
import { gamesInWeek } from './schedule'
import { weekDays, type ReplayWeek, type Season } from './season'

export const rivalsOf = (league: ReplayLeague) =>
  Object.keys(league.rosters).filter((t) => t !== league.me)

/** A simple round robin: week n meets rival (n − 1) mod 15, so every rival comes round in turn. */
export function defaultRival(league: ReplayLeague, week: number): string {
  const rivals = rivalsOf(league)
  return rivals[(week - 1) % rivals.length] ?? rivals[0] ?? ''
}

/** The first week without a kept result (or the last week once all are played). */
export function nextWeek(
  league: ReplayLeague,
  weeks: readonly ReplayWeek[],
): ReplayWeek | undefined {
  return weeks.find((w) => !league.results[String(w.week)]) ?? weeks[weeks.length - 1]
}

export function startWeek(league: ReplayLeague, week: ReplayWeek, rival: string): WeekState {
  const taken = new Set(Object.values(league.rosters).flat())
  return {
    days: weekDays(week),
    mine: league.rosters[league.me] ?? [],
    theirs: league.rosters[rival] ?? [],
    taken,
    moves: [],
    benched: new Map(),
  }
}

export type FreeAgent = { player: ReplayPlayer; games: number }

/** Players on no roster (counting this week's drops), most games this week first, then value. */
export function freeAgents(s: Season, state: WeekState, limit = 60): FreeAgent[] {
  const held = new Set(state.taken)
  for (const m of state.moves) {
    // in order: a player dropped and then picked up again is held
    held.add(m.add)
    held.delete(m.drop)
  }
  const out: FreeAgent[] = []
  for (const p of s.players.values()) {
    if (held.has(p.id)) continue
    const games = gamesInWeek(s, p.id, state.days)
    if (games > 0) out.push({ player: p, games })
  }
  return out
    .sort((a, b) => b.games - a.games || b.player.usd - a.player.usd || a.player.id - b.player.id)
    .slice(0, limit)
}

export function seasonRecord(league: ReplayLeague): { wins: number; losses: number; ties: number } {
  const r = { wins: 0, losses: 0, ties: 0 }
  for (const w of Object.values(league.results)) {
    if (w.wins > w.losses) r.wins += 1
    else if (w.wins < w.losses) r.losses += 1
    else r.ties += 1
  }
  return r
}

/** Keeps a played week: its result, and my roster after the week's pickups (they carry on). */
export function keepWeek(
  league: ReplayLeague,
  week: number,
  rival: string,
  state: WeekState,
  result: WeekResult,
): ReplayLeague {
  const record: WeekRecord = { opponent: rival, ...result.record }
  return {
    ...league,
    rosters: { ...league.rosters, [league.me]: rosterOn(state, state.days.length) },
    results: { ...league.results, [String(week)]: record },
  }
}

export const recordText = (r: { wins: number; losses: number; ties: number }) =>
  `${r.wins}-${r.losses}-${r.ties}`
