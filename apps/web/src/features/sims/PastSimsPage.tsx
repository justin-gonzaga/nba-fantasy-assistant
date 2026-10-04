// SIM-006: past sims, kept with the account — compare practice drafts (sort, filter, a trend), reopen a
// report, pin the references, and continue a replay season on any device.
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useSim, useSims, useSimsApi } from '../../api/client'
import { ApiError } from '../../api/http'
import type { SimFull, SimSummary } from '../../api/types'
import { Button, ButtonLink } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { PageHeader } from '../../components/ui/PageHeader'
import { QueryState } from '../../components/ui/QueryState'
import { ReportView, signed, type SavedReport } from '../draft/ReportView'
import { saveLeague, type ReplayLeague } from '../replay/league'
import {
  flush,
  flushLeagues,
  leagueSim,
  migrateHistory,
  pending,
  pendingLeagues,
  type RunSummary,
} from './sync'

const field = 'surface rounded-chip text-ink focus-visible:outline-2 focus-visible:outline-accent'
const select = cx(field, INTERACTIVE, 'min-h-11 w-full px-2.5 text-subhead')
const label = 'flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase'

type Row = SimSummary & { synced: boolean }
const day = (r: Row) => String((r.summary as Partial<RunSummary>).at ?? r.createdAt).slice(0, 10)

function Column({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-[880px] flex-col gap-4 px-5 pt-5 pb-8 min-[840px]:px-0 min-[840px]:pt-8">
      {children}
    </div>
  )
}

export function PastSimsPage() {
  const { sims, refresh } = useSimsApi()
  // Upload what this browser kept (earlier runs, anything saved offline), then re-read the list.
  useEffect(() => {
    migrateHistory()
    if (sims)
      void Promise.all([flush(sims), flushLeagues(sims)]).then(([a, b]) =>
        a + b > 0 ? refresh() : undefined,
      )
    // once per visit
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const q = useSims()
  return (
    <Column>
      <PageHeader title="Past sims" />
      {!sims && (
        <Card className="p-4 text-body text-ink-2">
          Sign in to keep your practice drafts and replay seasons with your account, on every
          device.
        </Card>
      )}
      <QueryState q={q}>{(list) => <Lists list={list} />}</QueryState>
    </Column>
  )
}

function Lists({ list }: { list: SimSummary[] }) {
  const [tab, setTab] = useState<'practice' | 'league'>('practice')
  const local = [...pending(), ...Object.values(pendingLeagues()).map(leagueSim)]
  const rows: Row[] = [
    ...local
      .filter((p) => p.kind === 'league' || !list.some((s) => s.id === p.id))
      .map((p) => ({
        ...p,
        pinned: false,
        hasDetail: false,
        createdAt: String((p.summary as Partial<RunSummary>).at ?? ''),
        updatedAt: '',
        version: 0,
        synced: false,
      })),
    // a league with unsynced progress shows once, as not synced yet
    ...list
      .filter((s) => !local.some((p) => p.kind === 'league' && p.id === s.id))
      .map((s) => ({ ...s, synced: true })),
  ]
  const practice = rows.filter((r) => r.kind === 'practice')
  const leagues = rows.filter((r) => r.kind === 'league')
  return (
    <>
      <div role="group" aria-label="Kind of sim" className="flex gap-2">
        <Button
          variant={tab === 'practice' ? 'primary' : 'secondary'}
          aria-pressed={tab === 'practice'}
          onClick={() => setTab('practice')}
        >
          Practice drafts ({practice.length})
        </Button>
        <Button
          variant={tab === 'league' ? 'primary' : 'secondary'}
          aria-pressed={tab === 'league'}
          onClick={() => setTab('league')}
        >
          Season replays ({leagues.length})
        </Button>
      </div>
      {tab === 'practice' ? <Practice rows={practice} /> : <Leagues rows={leagues} />}
    </>
  )
}

/** The surplus over the runs shown, oldest to newest: a simple line, with the numbers said aloud. */
function Trend({ rows }: { rows: Row[] }) {
  const pts = [...rows]
    .sort((a, b) => day(a).localeCompare(day(b)) || a.createdAt.localeCompare(b.createdAt))
    .slice(-20)
    .map((r) => Number((r.summary as Partial<RunSummary>).surplus ?? 0))
  if (pts.length < 2) return null
  const lo = Math.min(...pts, 0)
  const hi = Math.max(...pts, 0)
  const span = hi - lo || 1
  const x = (i: number) => 4 + (i / (pts.length - 1)) * 292
  const y = (v: number) => 4 + (1 - (v - lo) / span) * 52
  const line = pts.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const say = `Surplus over your last ${pts.length} runs: from ${signed(pts[0] ?? 0)} to ${signed(pts[pts.length - 1] ?? 0)}, best ${signed(hi)}.`
  return (
    <figure className="flex flex-col gap-1">
      <svg viewBox="0 0 300 60" className="h-16 w-full max-w-[420px]" role="img" aria-label={say}>
        <line x1="4" x2="296" y1={y(0)} y2={y(0)} className="stroke-line" strokeWidth="1" />
        <path d={line} fill="none" className="stroke-accent" strokeWidth="2" />
        {pts.map((v, i) => (
          <circle key={i} cx={x(i)} cy={y(v)} r="2.5" className="fill-accent" />
        ))}
      </svg>
      <figcaption className="text-caption text-muted">{say}</figcaption>
    </figure>
  )
}

function Practice({ rows }: { rows: Row[] }) {
  const { sims, refresh } = useSimsApi()
  const [sort, setSort] = useState<'new' | 'surplus' | 'wins'>('new')
  const [season, setSeason] = useState('all')
  const [strategy, setStrategy] = useState('all')
  const [confirm, setConfirm] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const seasons = [...new Set(rows.map((r) => r.season))].sort().reverse()
  const strategies = [...new Set(rows.map((r) => r.title))].sort()
  const shown = useMemo(() => {
    const val = (r: Row, k: keyof RunSummary) => Number((r.summary as Partial<RunSummary>)[k] ?? 0)
    return rows
      .filter(
        (r) =>
          (season === 'all' || r.season === season) && (strategy === 'all' || r.title === strategy),
      )
      .sort((a, b) =>
        sort === 'surplus'
          ? val(b, 'surplus') - val(a, 'surplus')
          : sort === 'wins'
            ? val(b, 'categoryWins') - val(a, 'categoryWins')
            : day(b).localeCompare(day(a)) || b.createdAt.localeCompare(a.createdAt),
      )
  }, [rows, season, strategy, sort])
  const act = async (f: () => Promise<unknown>) => {
    setError(null)
    try {
      await f()
      await refresh()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'That didn’t work. Try again.')
    }
  }
  if (rows.length === 0)
    return (
      <Card className="flex flex-col gap-2 p-4">
        <p className="text-headline">No practice drafts yet</p>
        <p className="text-body text-ink-2">
          Finished drafts in <Link to="/draft">Draft practice</Link> are kept here, so you can
          compare strategies before the real auction.
        </p>
      </Card>
    )
  return (
    <section aria-label="Practice drafts" className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-3">
        <label className={cx(label, 'min-w-[150px] flex-1')}>
          Sort
          <select
            className={select}
            value={sort}
            onChange={(e) => setSort(e.target.value as typeof sort)}
          >
            <option value="new">Newest first</option>
            <option value="surplus">Best surplus</option>
            <option value="wins">Most category wins</option>
          </select>
        </label>
        <label className={cx(label, 'min-w-[150px] flex-1')}>
          Season
          <select className={select} value={season} onChange={(e) => setSeason(e.target.value)}>
            <option value="all">All seasons</option>
            {seasons.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className={cx(label, 'min-w-[150px] flex-1')}>
          Strategy
          <select className={select} value={strategy} onChange={(e) => setStrategy(e.target.value)}>
            <option value="all">All strategies</option>
            {strategies.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>
      <Trend rows={shown} />
      {error && (
        <p role="alert" className="text-subhead text-lose">
          {error}
        </p>
      )}
      <ul aria-label="Your practice drafts" className="flex flex-col gap-2">
        {shown.map((r) => {
          const s = r.summary as Partial<RunSummary>
          return (
            <li key={r.id}>
              <Card className="flex flex-col gap-2 p-3">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-body font-semibold">{r.title}</span>
                    <span className="text-caption text-muted">
                      {day(r)} · {r.season}
                      {r.synced ? '' : ' · not synced yet'}
                      {r.synced && !r.hasDetail ? ' · summary only' : ''}
                    </span>
                  </span>
                  <span className="text-subhead tabular-nums">
                    {signed(Number(s.surplus ?? 0))}
                  </span>
                  <span className="text-subhead text-ink-2 tabular-nums">
                    {Number(s.categoryWins ?? 0).toFixed(1)}
                    {s.counted ? ` of ${s.counted}` : ''} wins
                  </span>
                </div>
                {r.synced && sims && (
                  <div className="flex flex-wrap gap-2">
                    <ButtonLink to={`/sims/${encodeURIComponent(r.id)}`}>Open</ButtonLink>
                    <Button
                      variant="secondary"
                      aria-pressed={r.pinned}
                      aria-label={`${r.pinned ? 'Unpin' : 'Pin'} ${r.title}, ${day(r)}`}
                      onClick={() => void act(() => sims.pin(r.id, !r.pinned))}
                    >
                      {r.pinned ? 'Pinned' : 'Pin'}
                    </Button>
                    {confirm === r.id ? (
                      <span role="group" aria-label="Delete this run?" className="flex gap-2">
                        <Button
                          onClick={() =>
                            void act(() => sims.remove(r.id)).then(() => setConfirm(null))
                          }
                        >
                          Delete
                        </Button>
                        <Button variant="secondary" onClick={() => setConfirm(null)}>
                          Keep
                        </Button>
                      </span>
                    ) : (
                      <Button variant="secondary" onClick={() => setConfirm(r.id)}>
                        Delete…
                      </Button>
                    )}
                  </div>
                )}
              </Card>
            </li>
          )
        })}
      </ul>
      <p className="text-caption text-muted">
        Your latest 30 runs keep their full report; older ones keep a summary (up to 200). Pin up to
        10 to keep them in full.
      </p>
    </section>
  )
}

function Leagues({ rows }: { rows: Row[] }) {
  const { sims, refresh } = useSimsApi()
  const navigate = useNavigate()
  const [confirm, setConfirm] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (rows.length === 0)
    return (
      <Card className="flex flex-col gap-2 p-4">
        <p className="text-headline">No season replays yet</p>
        <p className="text-body text-ink-2">
          Draft on a past season in <Link to="/draft">Draft practice</Link>, then play it week by
          week.
        </p>
      </Card>
    )
  const resume = async (id: string) => {
    setError(null)
    try {
      const { sim } = (await sims?.get(id)) ?? {}
      if (!sim?.detail) throw new Error('missing')
      saveLeague(sim.detail as unknown as ReplayLeague)
      void navigate('/replay')
    } catch {
      setError('That season couldn’t be loaded. Try again.')
    }
  }
  return (
    <section aria-label="Season replays" className="flex flex-col gap-2">
      {error && (
        <p role="alert" className="text-subhead text-lose">
          {error}
        </p>
      )}
      <ul aria-label="Your season replays" className="flex flex-col gap-2">
        {rows.map((r) => {
          const s = r.summary as {
            record?: { wins: number; losses: number; ties: number }
            weeksKept?: number
          }
          const rec = s.record ?? { wins: 0, losses: 0, ties: 0 }
          return (
            <li key={r.id}>
              <Card className="flex flex-col gap-2 p-3">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-body font-semibold">{r.title}</span>
                    <span className="text-caption text-muted">
                      {s.weeksKept ?? 0} weeks played{r.synced ? '' : ' · not synced yet'}
                    </span>
                  </span>
                  <span className="text-headline font-semibold tabular-nums">
                    {rec.wins}-{rec.losses}-{rec.ties}
                  </span>
                </div>
                {r.synced && sims && (
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => void resume(r.id)}>Continue</Button>
                    {confirm === r.id ? (
                      <span role="group" aria-label="Delete this season?" className="flex gap-2">
                        <Button
                          onClick={() =>
                            void sims
                              .remove(r.id)
                              .then(refresh)
                              .then(() => setConfirm(null))
                          }
                        >
                          Delete
                        </Button>
                        <Button variant="secondary" onClick={() => setConfirm(null)}>
                          Keep
                        </Button>
                      </span>
                    ) : (
                      <Button variant="secondary" onClick={() => setConfirm(r.id)}>
                        Delete…
                      </Button>
                    )}
                  </div>
                )}
              </Card>
            </li>
          )
        })}
      </ul>
      <p className="text-caption text-muted">You can keep 5 season replays.</p>
    </section>
  )
}

/** /sims/:id — one saved run's report, as it was. */
export function SimDetailPage() {
  const { id = '' } = useParams()
  const q = useSim(id)
  return (
    <Column>
      <QueryState q={q}>{(sim) => <Detail sim={sim} />}</QueryState>
    </Column>
  )
}

function Detail({ sim }: { sim: SimFull }) {
  const s = sim.summary as Partial<RunSummary>
  const saved = sim.detail as (SavedReport & { version?: number }) | null
  return (
    <>
      <PageHeader
        eyebrow={`${String(s.at ?? sim.createdAt).slice(0, 10)} · ${sim.season}`}
        title={sim.title}
      />
      {saved?.report ? (
        <ReportView report={saved.report} names={saved.names ?? {}} team={saved.team ?? []} />
      ) : (
        <Card className="flex flex-col gap-2 p-4">
          <p className="text-headline">
            Surplus {signed(Number(s.surplus ?? 0))} · {Number(s.categoryWins ?? 0).toFixed(1)}{' '}
            category wins
          </p>
          <p className="text-body text-ink-2">
            Only the summary is kept for this run: it is older than your latest 30, or it was saved
            before full reports were kept. Pin a run to keep its full report.
          </p>
        </Card>
      )}
      <ButtonLink to="/sims" variant="secondary">
        Back to past sims
      </ButtonLink>
    </>
  )
}
