import type { ReplayDoc } from '../season'

const z = [0, 0, 0, 0, 0, 0, 0, 0, 0]
/** A two-week season: three players, three games. */
export const tinyDoc = (): ReplayDoc => ({
  season: '2024-25',
  method: 'ours',
  players: [
    { id: 10, name: 'Ann Guard', team: 'BOS', pos: 'G', usd: 40, rank: 1, z },
    { id: 20, name: 'Bo Center', team: 'LAL', pos: 'C', usd: 12.5, rank: 2, z },
    { id: 30, name: 'Cy Bench', team: 'NYK', pos: 'F', usd: 0, rank: null, z },
  ],
  weeks: [
    { week: 1, start: '2024-10-22', end: '2024-10-27' },
    { week: 2, start: '2024-10-28', end: '2024-11-03' },
  ],
  lines: {
    dates: ['2024-10-22', '2024-10-24'],
    players: [10, 30, 10],
    day: [0, 0, 1],
    min: [34, 12, 30],
    pts: [25, 4, 18],
    reb: [5, 3, 4],
    ast: [7, 0, 6],
    stl: [1, 0, 2],
    blk: [0, 1, 0],
    fg3m: [3, 0, 2],
    tov: [2, 1, 3],
    fgm: [9, 2, 7],
    fga: [18, 5, 15],
    ftm: [4, 0, 2],
    fta: [5, 0, 2],
  },
})
