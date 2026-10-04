// SIM-004: a side's week at a glance — each player × day: a game or not, and whether he starts. On my side
// a game cell is a button: bench him that day (or start him again). The auto lineup fills the slots.
import { cx } from '../../components/ui/interactive'
import { Avatar } from '../../components/ui/Avatar'
import { headshotUrl } from '../players/format'
import type { ReplayPlayer } from './matchup'

export type CellState = 'start' | 'bench' | 'off' | 'none' | 'away'

export const dayLabel = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', {
    weekday: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })

const LOOK: Record<CellState, { text: string; say: string; className: string }> = {
  start: { text: 'Start', say: 'starts', className: 'badge-win' },
  bench: {
    text: 'Bench',
    say: 'has a game but no open slot',
    className: 'bg-surface-2 text-ink-2',
  },
  off: { text: 'Off', say: 'benched by you', className: 'badge-warn' },
  none: { text: '–', say: 'no game', className: 'text-muted' },
  away: { text: '', say: 'not on the roster yet', className: '' },
}

export function ScheduleGrid({
  caption,
  rows,
  days,
  players,
  cell,
  games,
  onToggle,
}: {
  caption: string
  rows: readonly number[]
  days: readonly string[]
  players: ReadonlyMap<number, ReplayPlayer>
  cell: (pid: number, day: number) => CellState
  games: (pid: number) => number
  onToggle?: (pid: number, day: number) => void
}) {
  const starts = days.map((_, d) => rows.filter((pid) => cell(pid, d) === 'start').length)
  return (
    // Scrolls sideways on a phone: focusable and named, so the keyboard can scroll it too (axe).
    <div
      role="region"
      aria-label={caption}
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- a scroll region must be focusable (WCAG 2.1.1, axe scrollable-region-focusable)
      tabIndex={0}
      className="-mx-4 overflow-x-auto px-4 focus-visible:outline-2 focus-visible:outline-accent"
    >
      <table className="w-full min-w-[560px] border-separate border-spacing-y-1 text-subhead">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="text-caption tracking-eyebrow text-muted uppercase">
            <th scope="col" className="text-left font-semibold">
              Player
            </th>
            <th scope="col" className="w-12 text-right font-semibold">
              G
            </th>
            {days.map((d) => (
              <th key={d} scope="col" className="w-16 text-center font-semibold">
                {dayLabel(d)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((pid) => {
            const p = players.get(pid)
            const name = p?.name ?? `Player ${pid}`
            return (
              <tr key={pid}>
                <th scope="row" className="text-left font-normal">
                  <span className="flex min-w-0 items-center gap-2">
                    <Avatar src={headshotUrl(pid)} name={name} size={28} />
                    <span className="flex min-w-0 flex-col">
                      <span className="truncate font-semibold">{name}</span>
                      <span className="truncate text-caption text-muted">
                        {[p?.team, p?.pos ?? 'Util'].filter(Boolean).join(' · ')}
                      </span>
                    </span>
                  </span>
                </th>
                <td className="text-right tabular-nums">{games(pid)}</td>
                {days.map((d, i) => {
                  const st = cell(pid, i)
                  const look = LOOK[st]
                  const label = `${name}, ${dayLabel(d)}: ${look.say}`
                  const canToggle = onToggle && (st === 'start' || st === 'bench' || st === 'off')
                  return (
                    <td key={d} className="text-center">
                      {canToggle ? (
                        <button
                          type="button"
                          aria-label={`${label}. ${st === 'off' ? 'Start him' : 'Bench him'}`}
                          aria-pressed={st === 'off'}
                          onClick={() => onToggle(pid, i)}
                          className={cx(
                            'min-h-11 w-full cursor-pointer rounded-chip px-1 text-caption font-semibold',
                            'focus-visible:outline-2 focus-visible:outline-accent',
                            look.className,
                          )}
                        >
                          {look.text}
                        </button>
                      ) : (
                        <span
                          aria-label={label}
                          role="img"
                          className={cx(
                            'inline-flex min-h-8 w-full items-center justify-center rounded-chip text-caption font-semibold',
                            look.className,
                          )}
                        >
                          {look.text}
                        </span>
                      )}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr className="text-caption text-muted">
            <th scope="row" className="text-left font-semibold">
              Starts
            </th>
            <td className="text-right tabular-nums">{starts.reduce((a, b) => a + b, 0)}</td>
            {starts.map((n, i) => (
              <td key={days[i]} className="text-center tabular-nums">
                {n}
              </td>
            ))}
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
