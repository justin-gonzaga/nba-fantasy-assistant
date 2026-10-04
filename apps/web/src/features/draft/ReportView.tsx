// The practice-draft report as a view of stored data (SIM-006): the finished draft shows it, and a saved run
// reopens it from the account exactly as it was.
import { useId, type ReactNode } from 'react'
import { Card } from '../../components/ui/Card'
import { cx } from '../../components/ui/interactive'
import { loadFx, prefersReducedMotion } from './fx/prefs'
import type { Report } from './report'

export type TeamRow = { pid: string; price: number; value: number }

/** What a saved practice run keeps to show its report again (no player list needed). */
export type SavedReport = {
  report: Report
  names: Record<string, string>
  team: TeamRow[]
}

function Stat({ label: l, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="text-caption tracking-eyebrow text-muted uppercase">{l}</span>
      <span className="text-headline font-semibold tabular-nums">{value}</span>
    </span>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  const id = useId()
  return (
    <section aria-labelledby={id}>
      <Card className="flex flex-col gap-3 p-4">
        <h2 id={id} className="text-caption font-semibold tracking-eyebrow text-muted uppercase">
          {title}
        </h2>
        {children}
      </Card>
    </section>
  )
}

export const signed = (n: number) => `${n >= 0 ? '+' : '−'}$${Math.abs(n)}`

export function ReportView({ report: r, names, team }: SavedReport) {
  const name = (pid: string) => names[pid] ?? `Player ${pid}`
  const counted = r.categories.filter((c) => !c.punted).length
  const reduceMotion = prefersReducedMotion(loadFx())
  return (
    <>
      <div className="flex flex-wrap gap-x-6 gap-y-2">
        <Stat label="Spent" value={`$${r.spent}`} />
        <Stat label="Team value" value={`$${r.value}`} />
        <Stat label="Surplus" value={signed(r.surplus)} />
        <Stat label="Category wins" value={`${r.categoryWins} of ${counted}`} />
      </div>

      {r.lessons.length > 0 && (
        <Section title="What to take into the real draft">
          <ol aria-label="Lessons" className="flex list-decimal flex-col gap-2 pl-5 text-body">
            {r.lessons.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ol>
        </Section>
      )}

      <div className="grid gap-4 min-[840px]:grid-cols-2">
        <Section title="Categories against the room">
          <ul aria-label="Category ranks" className="flex flex-col gap-1.5">
            {r.categories.map((c) => (
              <li
                key={c.key}
                className="grid grid-cols-[48px_1fr_64px] items-center gap-3 text-subhead"
              >
                <span className="font-medium">{c.label}</span>
                <span
                  className="relative h-1.5 overflow-hidden rounded-full bg-line"
                  aria-hidden="true"
                >
                  {!c.punted && (
                    <span
                      className={cx(
                        !reduceMotion && 'bar-grow',
                        'absolute inset-y-0 left-0 rounded-full',
                        c.rank <= 5 ? 'bg-win' : c.rank >= 12 ? 'bg-lose' : 'bg-even',
                      )}
                      style={{ width: `${((17 - c.rank) / 16) * 100}%` }}
                    />
                  )}
                </span>
                <span className="text-right tabular-nums">
                  {c.punted ? 'punted' : `${c.rank} of 16`}
                </span>
              </li>
            ))}
          </ul>
          <p className="text-caption text-muted">
            Ranks use your players&apos; summed category strengths against the 15 rivals. Category
            wins count the share of rivals you beat in each category, from season projections
            (weekly swings aren&apos;t modelled here).
          </p>
        </Section>
        <Section title="Budget pace">
          <table className="w-full text-subhead">
            <caption className="sr-only">Your spending against the average rival</caption>
            <thead>
              <tr className="text-caption text-muted">
                <th scope="col" className="text-left font-medium">
                  After sale
                </th>
                <th scope="col" className="text-right font-medium">
                  You
                </th>
                <th scope="col" className="text-right font-medium">
                  Average team
                </th>
              </tr>
            </thead>
            <tbody>
              {r.pace.map((x) => (
                <tr key={x.sale} className="border-t border-line">
                  <th scope="row" className="py-1.5 text-left font-normal tabular-nums">
                    {x.sale}
                  </th>
                  <td className="text-right tabular-nums">${x.mine}</td>
                  <td className="text-right text-muted tabular-nums">${x.room}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {(r.bestBuys.length > 0 || r.overpays.length > 0) && (
            <dl className="grid grid-cols-2 gap-3 pt-1 text-subhead">
              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted">Best buys</dt>
                {r.bestBuys.map((b) => (
                  <dd key={b.pid}>
                    {name(b.pid)} <span className="text-win tabular-nums">{signed(b.diff)}</span>
                  </dd>
                ))}
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted">Overpays</dt>
                {r.overpays.map((b) => (
                  <dd key={b.pid}>
                    {name(b.pid)} <span className="text-lose tabular-nums">{signed(b.diff)}</span>
                  </dd>
                ))}
              </div>
            </dl>
          )}
        </Section>
      </div>

      <Section title={`Your team · ${team.length} players`}>
        <table className="w-full text-subhead">
          <caption className="sr-only">Your drafted team</caption>
          <thead>
            <tr className="text-caption text-muted">
              <th scope="col" className="text-left font-medium">
                Player
              </th>
              <th scope="col" className="text-right font-medium">
                Paid
              </th>
              <th scope="col" className="text-right font-medium">
                Value
              </th>
            </tr>
          </thead>
          <tbody>
            {team.map((s) => (
              <tr key={s.pid} className="border-t border-line">
                <th scope="row" className="py-1.5 text-left font-normal">
                  {name(s.pid)}
                </th>
                <td className="text-right tabular-nums">${s.price}</td>
                <td className="text-right text-muted tabular-nums">${Math.round(s.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  )
}
