import values from '../../draft/fixtures/values-2026-27.json' with { type: 'json' }
import type { ReplayDoc } from '../season'

const POS = ['G', 'F', 'C', 'G-F', 'F-C'] as const

/** A replay file built from the 2026-27 values fixture: a full pool under replay names, no games. */
export function replayDoc(season: string): ReplayDoc {
  return {
    season,
    method: 'ours',
    players: values.players.map((v, i) => ({
      id: Number(v.id),
      name: `Replay ${v.id}`,
      team: 'TST',
      pos: POS[i % POS.length] ?? 'G',
      usd: v.usd,
      rank: i + 1,
      z: v.z,
    })),
    weeks: [],
    lines: {
      dates: [],
      players: [],
      day: [],
      min: [],
      pts: [],
      reb: [],
      ast: [],
      stl: [],
      blk: [],
      fg3m: [],
      tov: [],
      fgm: [],
      fga: [],
      ftm: [],
      fta: [],
    },
  }
}
