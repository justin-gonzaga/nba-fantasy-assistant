// WEB-024: the ≥ 840 px Players table (design-language §9 tables).
import type { PlayerRow } from '../../api/types'
import { Avatar } from '../../components/ui/Avatar'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { RowBadges } from './PlayerBadges'
import { MIN_MPG, headshotUrl, inRotation, pct } from './format'

export type SortDir = 'asc' | 'desc'

type Projection = NonNullable<PlayerRow['projection']>

/** The stat columns: the URL sort key (a category strength), the header and the projected figure. */
export const STAT_COLUMNS: [string, string, (p: Projection) => string][] = [
  ['pts', 'PTS', (p) => p.pts.toFixed(1)],
  ['reb', 'REB', (p) => p.reb.toFixed(1)],
  ['ast', 'AST', (p) => p.ast.toFixed(1)],
  ['stl', 'STL', (p) => p.stl.toFixed(1)],
  ['blk', 'BLK', (p) => p.blk.toFixed(1)],
  ['fg3m', '3PM', (p) => p.fg3m.toFixed(1)],
  ['fg_pct', 'FG%', (p) => pct(p.fgPct)],
  ['ft_pct', 'FT%', (p) => pct(p.ftPct)],
  ['tov', 'TO', (p) => p.tov.toFixed(1)],
]

const th = 'sticky top-0 z-[1] bg-surface px-2 py-2 text-caption font-medium text-muted'

function SortHeader({
  k,
  label,
  sort,
  dir,
  onSort,
  align = 'right',
}: {
  k: string
  label: string
  sort: string
  dir: SortDir
  onSort: (key: string) => void
  align?: 'left' | 'right'
}) {
  const active = sort === k
  return (
    <th
      scope="col"
      aria-sort={active ? (dir === 'asc' ? 'ascending' : 'descending') : undefined}
      className={cx(th, align === 'right' ? 'text-right' : 'text-left')}
    >
      <button
        type="button"
        onClick={() => onSort(k)}
        className={cx(
          INTERACTIVE,
          'inline-flex items-center gap-0.5 rounded-chip hover:text-ink',
          active && 'font-semibold text-ink',
        )}
      >
        {label}
        <span aria-hidden="true" className={cx('w-2', !active && 'invisible')}>
          {dir === 'asc' ? '▲' : '▼'}
        </span>
      </button>
    </th>
  )
}

export function PlayersTable({
  players,
  sort,
  dir,
  onSort,
  onOpen,
  selectedId,
  busy,
  compact = false,
}: {
  players: PlayerRow[]
  sort: string
  dir: SortDir
  onSort: (key: string) => void
  onOpen: (p: PlayerRow, trigger: HTMLButtonElement) => void
  selectedId: number | null
  busy: boolean
  /** Beside an open panel on a narrower screen: #, Player and $ only (the panel has the stat line). */
  compact?: boolean
}) {
  const stats = compact ? [] : STAT_COLUMNS
  const header = { sort, dir, onSort }
  return (
    <div className="surface overflow-x-auto rounded-card">
      <table aria-label="Players" aria-busy={busy} className="w-full border-collapse">
        <thead>
          <tr className="border-b border-line">
            <SortHeader k="rank" label="#" {...header} />
            <th scope="col" className={cx(th, 'text-left')}>
              Player
            </th>
            <SortHeader k="dollars" label="$" {...header} />
            {stats.map(([k, label]) => (
              <SortHeader key={k} k={k} label={label} {...header} />
            ))}
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr
              key={p.id}
              data-selected={p.id === selectedId ? 'true' : undefined}
              onClick={(e) => {
                const b = e.currentTarget.querySelector('button')
                if (b && !(e.target as HTMLElement).closest('button')) onOpen(p, b)
              }}
              className={cx(
                'cursor-pointer text-subhead transition-colors even:bg-ground/60 hover:bg-surface-2',
                p.id === selectedId && 'bg-surface-2 even:bg-surface-2',
              )}
            >
              <td
                className={cx(
                  'border-l-2 px-2 py-2 text-right text-muted tabular-nums',
                  p.id === selectedId ? 'border-accent' : 'border-transparent',
                )}
              >
                {p.rank}
              </td>
              <td className="max-w-0 min-w-56 px-2 py-2">
                <div className="flex items-center gap-2.5">
                  <Avatar src={headshotUrl(p.id)} name={p.name} size={32} />
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <button
                      type="button"
                      onClick={(e) => onOpen(p, e.currentTarget)}
                      className={cx(
                        INTERACTIVE,
                        'truncate rounded-chip text-left text-body font-semibold',
                      )}
                    >
                      {p.name}
                    </button>
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      {(p.team || p.positions) && (
                        <span className="text-caption text-muted">
                          {[p.team, p.positions].filter(Boolean).join(' · ')}
                        </span>
                      )}
                      <RowBadges player={p} />
                    </span>
                  </div>
                </div>
              </td>
              <td
                className={cx(
                  'px-2 py-2 text-right font-semibold tabular-nums',
                  !p.inPool && 'font-normal text-muted',
                )}
              >
                ${Math.round(p.dollars)}
              </td>
              {stats.map(([k, , fmt]) => (
                <td
                  key={k}
                  title={inRotation(p) ? undefined : `Under ${MIN_MPG} min/game projected`}
                  className={cx(
                    'px-2 py-2 text-right tabular-nums',
                    inRotation(p) ? 'text-ink-2' : 'text-muted',
                  )}
                >
                  {p.projection ? fmt(p.projection) : '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
