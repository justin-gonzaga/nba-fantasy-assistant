// Pure helpers for the player explorer (WEB-005).

export const CATEGORIES = [
  ['pts', 'PTS'],
  ['reb', 'REB'],
  ['ast', 'AST'],
  ['stl', 'STL'],
  ['blk', 'BLK'],
  ['fg3m', '3PM'],
  ['fg_pct', 'FG%'],
  ['ft_pct', 'FT%'],
  ['tov', 'TOV'],
] as const

/** WEB-027: the rotation floor. Below it a player's category figures aren't ranked (TO rewards sitting). */
export const MIN_MPG = 20
export const CATEGORY_KEYS: ReadonlySet<string> = new Set(CATEGORIES.map(([k]) => k))
export const inRotation = (p: { projection: { mpg: number } | null }) =>
  (p.projection?.mpg ?? 0) >= MIN_MPG

const CATEGORY_LABEL: Record<string, string> = Object.fromEntries(CATEGORIES)

/** `all` → "All categories", `punt_fg_pct` → "Punt FG%". */
export function strategyLabel(variant: string): string {
  if (variant === 'all') return 'All categories'
  const cat = variant.replace(/^punt_/, '')
  return `Punt ${CATEGORY_LABEL[cat] ?? cat.toUpperCase()}`
}

// Letters NFD doesn't decompose (Đ, ø, ł, ß…) still need to match plain-ASCII typing.
const EXTRA: Record<string, string> = { đ: 'd', ø: 'o', ł: 'l', ß: 'ss', æ: 'ae', œ: 'oe', ı: 'i' }

/** Lower-case, accent-free text for matching: "Jokić" and "jokic" compare equal. */
export function fold(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/[đøłßæœı]/g, (c) => EXTRA[c] ?? c)
}

/** Whether NBA positions like "F-C" include the chip's group. */
export function hasPosition(positions: string | null, group: string): boolean {
  return positions !== null && positions.split('-').includes(group)
}

export const headshotUrl = (id: number) =>
  `https://cdn.nba.com/headshots/nba/latest/260x190/${id}.png`

/** .490 style, as box scores print shooting percentages. */
export const pct = (x: number | null) => (x === null ? '—' : x.toFixed(3).replace(/^0/, ''))

/** A signed standardized value with a real minus sign: +2.80 / −1.40. */
export const signed = (x: number) => `${x < 0 ? '−' : '+'}${Math.abs(x).toFixed(2)}`
