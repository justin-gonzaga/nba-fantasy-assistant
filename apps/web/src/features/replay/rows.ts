// SIM-002: a replay season's players as the draft page's rows (names, team, position, value). Only
// pre-season facts: no projection, badges or in-season status, so the draft can't see the future.

import type { PlayerRow } from '../../api/types'
import { CATEGORIES } from '../players/format'
import type { Season } from './season'

export function replayRows(s: Season): Map<string, PlayerRow> {
  const rows = new Map<string, PlayerRow>()
  for (const p of s.players.values())
    rows.set(String(p.id), {
      id: p.id,
      name: p.name,
      team: p.team,
      positions: p.pos,
      dollars: p.usd,
      value: p.usd,
      rank: p.rank ?? 999,
      tier: 0,
      inPool: p.rank !== null,
      status: null,
      projection: null,
      badges: [],
      indicators: [],
      strengths: Object.fromEntries(CATEGORIES.map(([k], i) => [k, p.z[i] ?? 0])),
    })
  return rows
}
