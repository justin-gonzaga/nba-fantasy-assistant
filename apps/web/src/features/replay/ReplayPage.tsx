// SIM-004: play a replayed season week by week — choose the week and rival, read the schedule, set lineups,
// make up to 4 pickups, then play the week on the real box scores. G-31: rivals auto-start and never pick up.
import { useEffect, useId, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { useReplaySeason, useSimsApi } from '../../api/client'
import { flushLeagues, syncLeague } from '../sims/sync'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { PageHeader } from '../../components/ui/PageHeader'
import { QueryState } from '../../components/ui/QueryState'
import { loadLeague, saveLeague, type ReplayLeague } from './league'
import {
  MAX_ADDS,
  addPlayer,
  playWeek,
  rosterOn,
  type CategoryResult,
  type WeekResult,
  type WeekState,
} from './matchup'
import { ScheduleGrid, dayLabel, type CellState } from './ScheduleGrid'
import { gamesInWeek, hasGame, projectedLines, teamGamesInWeek, teamNames } from './schedule'
import { parseSeason, type ReplayDoc, type ReplayWeek, type Season } from './season'
import {
  defaultRival,
  freeAgents,
  keepWeek,
  nextWeek,
  recordText,
  rivalsOf,
  seasonRecord,
  startWeek,
} from './week'

const field = 'surface rounded-chip text-ink focus-visible:outline-2 focus-visible:outline-accent'
const select = cx(field, INTERACTIVE, 'min-h-11 w-full px-2.5 text-subhead')
const label = 'flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase'

export function ReplayPage() {
  const [league, setLeague] = useState(loadLeague)
  const { sims, refresh } = useSimsApi()
  // A week kept offline earlier goes up now, through the same merge.
  useEffect(() => {
    if (sims) void flushLeagues(sims).then((n) => (n > 0 ? refresh() : undefined))
    // once per visit
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const q = useReplaySeason(league?.season ?? null)
  if (!league)
    return (
      <Column>
        <PageHeader title="Season replay" />
        <Card className="flex flex-col gap-2 p-4">
          <p className="text-headline">No replay league yet</p>
          <p className="text-body text-ink-2">
            Draft on a past season in <Link to="/draft">Draft practice</Link>, then choose
            &ldquo;Play the season&rdquo;.
          </p>
        </Card>
      </Column>
    )
  return (
    <QueryState
      q={q}
      notReady={{
        title: `The ${league.season} season isn't published yet`,
        body: 'It appears after the next daily update.',
      }}
    >
      {(doc) => (
        <Sim
          league={league}
          doc={doc as ReplayDoc}
          onKeep={(next) => {
            saveLeague(next)
            setLeague(next)
            if (sims)
              void syncLeague(sims, next).then((kept) => {
                if (kept !== next) {
                  saveLeague(kept) // another device was further on
                  setLeague(kept)
                }
                void refresh()
              })
          }}
        />
      )}
    </QueryState>
  )
}

function Column({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-4 px-5 pt-5 pb-8 min-[840px]:px-0 min-[840px]:pt-8">
      {children}
    </div>
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

function Stat({ label: l, value }: { label: string; value: string }) {
  return (
    <span className="flex min-h-11 items-center gap-1.5">
      <span className="text-caption tracking-eyebrow text-muted uppercase">{l}</span>
      <span className="text-headline font-semibold tabular-nums">{value}</span>
    </span>
  )
}

function Sim({
  league,
  doc,
  onKeep,
}: {
  league: ReplayLeague
  doc: ReplayDoc
  onKeep: (l: ReplayLeague) => void
}) {
  const s = useMemo(() => parseSeason(doc), [doc])
  const first = nextWeek(league, s.weeks)
  const [weekNo, setWeekNo] = useState(first?.week ?? 1)
  const week = s.weeks.find((w) => w.week === weekNo) ?? first
  const [rival, setRival] = useState(defaultRival(league, weekNo))
  if (!week)
    return (
      <Column>
        <PageHeader title="Season replay" />
        <Card className="p-4 text-body">This season&apos;s file has no weeks.</Card>
      </Column>
    )
  const choose = (w: number, r: string) => {
    setWeekNo(w)
    setRival(r)
  }
  return (
    <Column>
      <PageHeader eyebrow={`${s.season} replay`} title={`Week ${week.week} vs ${rival}`} />
      <div className="flex flex-wrap items-end gap-4">
        <label className={cx(label, 'min-w-[220px] flex-1')}>
          Week
          <select
            className={select}
            value={week.week}
            onChange={(e) => {
              const w = Number(e.target.value)
              choose(w, defaultRival(league, w))
            }}
          >
            {s.weeks.map((w) => {
              const kept = league.results[String(w.week)]
              return (
                <option key={w.week} value={w.week}>
                  Week {w.week} · {dayLabel(w.start)} – {dayLabel(w.end)}
                  {kept ? ` · ${recordText(kept)} vs ${kept.opponent}` : ''}
                </option>
              )
            })}
          </select>
        </label>
        <label className={cx(label, 'min-w-[180px] flex-1')}>
          Rival
          <select
            className={select}
            value={rival}
            onChange={(e) => choose(week.week, e.target.value)}
          >
            {rivalsOf(league).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <Stat label="Season" value={recordText(seasonRecord(league))} />
      </div>
      <WeekView
        key={`${week.week}|${rival}|${Object.keys(league.results).length}`}
        s={s}
        league={league}
        week={week}
        rival={rival}
        onKeep={onKeep}
      />
    </Column>
  )
}

const fmt = (key: string, v: number) =>
  key.endsWith('_pct') ? v.toFixed(3).replace(/^0/, '') : String(Math.round(v))

function WeekView({
  s,
  league,
  week,
  rival,
  onKeep,
}: {
  s: Season
  league: ReplayLeague
  week: ReplayWeek
  rival: string
  onKeep: (l: ReplayLeague) => void
}) {
  const [state, setState] = useState<WeekState>(() => startWeek(league, week, rival))
  const [result, setResult] = useState<WeekResult | null>(null)
  const kept = league.results[String(week.week)]
  const game = (pid: number, d: string) => hasGame(s, pid, d)
  const ids = [...new Set([...state.mine, ...state.theirs, ...state.moves.map((m) => m.add)])]
  const expected = projectedLines(s, ids, state.days)
  const hasHistory = [...expected.values()].some((d) => d.size > 0)
  const projected = playWeek(state, s.players, expected, game)
  const mineRows = [...new Set([...state.mine, ...state.moves.map((m) => m.add)])]

  const cell =
    (side: 'mine' | 'theirs') =>
    (pid: number, d: number): CellState => {
      const day = state.days[d] ?? ''
      if (side === 'mine' && !rosterOn(state, d).includes(pid)) return 'away'
      if (!game(pid, day)) return 'none'
      if (side === 'mine' && state.benched.get(d)?.has(pid)) return 'off'
      return projected.days[d]?.[side].includes(pid) ? 'start' : 'bench'
    }
  const toggle = (pid: number, d: number) => {
    const benched = new Map(state.benched)
    const day = new Set(benched.get(d) ?? [])
    if (day.has(pid)) day.delete(pid)
    else day.add(pid)
    benched.set(d, day)
    setState({ ...state, benched })
  }

  return (
    <div className="flex flex-col gap-4">
      {kept && (
        <Card className="p-4 text-body">
          You kept <strong>{recordText(kept)}</strong> against {kept.opponent} this week. Playing it
          again is practice only: it won&apos;t change your season.
        </Card>
      )}
      {result ? (
        <Result
          s={s}
          state={state}
          result={result}
          kept={Boolean(kept)}
          onKeep={() => onKeep(keepWeek(league, week.week, rival, state, result))}
          onBack={() => setResult(null)}
        />
      ) : (
        <Section title="Projected categories">
          {hasHistory ? (
            <>
              <CategoryTable rows={projected.categories} caption="Projected categories" />
              <p className="text-caption text-muted">
                From each player&apos;s averages in games before this week, on his scheduled games.
                Projected {recordText(projected.record)}.
              </p>
            </>
          ) : (
            <p className="text-body text-ink-2">
              No games have been played before this week, so there&apos;s nothing to project from
              yet. Go by the schedule: who plays most this week.
            </p>
          )}
          <Button onClick={() => setResult(playWeek(state, s.players, s.lines, game))}>
            Play the week
          </Button>
        </Section>
      )}
      <Section title="Your team: schedule and lineup">
        <p className="text-caption text-muted">
          The best players with a game start each day. Tap a day to bench a player; tap again to
          start him.
        </p>
        <ScheduleGrid
          caption="Your team’s week"
          rows={mineRows}
          days={state.days}
          players={s.players}
          cell={cell('mine')}
          games={(pid) => gamesInWeek(s, pid, state.days)}
          onToggle={result ? undefined : toggle}
        />
      </Section>
      <Waivers s={s} state={state} setState={setState} disabled={result !== null} />
      <Section title={`${rival}: schedule`}>
        <p className="text-caption text-muted">
          Rivals start their best players each day and make no pickups.
        </p>
        <ScheduleGrid
          caption={`${rival}’s week`}
          rows={state.theirs}
          days={state.days}
          players={s.players}
          cell={cell('theirs')}
          games={(pid) => gamesInWeek(s, pid, state.days)}
        />
      </Section>
    </div>
  )
}

function CategoryTable({ rows, caption }: { rows: CategoryResult[]; caption: string }) {
  const mark = { win: 'badge-win', loss: 'badge-lose', tie: 'bg-surface-2 text-ink-2' } as const
  return (
    <table className="w-full text-subhead">
      <caption className="sr-only">{caption}</caption>
      <thead>
        <tr className="text-caption tracking-eyebrow text-muted uppercase">
          <th scope="col" className="text-left font-semibold">
            Category
          </th>
          <th scope="col" className="text-right font-semibold">
            You
          </th>
          <th scope="col" className="text-right font-semibold">
            Them
          </th>
          <th scope="col" className="w-20 text-right font-semibold">
            Result
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((c) => (
          <tr key={c.key}>
            <th scope="row" className="py-1 text-left font-semibold">
              {c.label}
            </th>
            <td className="text-right tabular-nums">{fmt(c.key, c.mine)}</td>
            <td className="text-right tabular-nums">{fmt(c.key, c.theirs)}</td>
            <td className="text-right">
              <span
                className={cx(
                  'rounded-chip px-2 py-0.5 text-caption font-semibold',
                  mark[c.result],
                )}
              >
                {c.result === 'win' ? 'Win' : c.result === 'loss' ? 'Loss' : 'Tie'}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Waivers({
  s,
  state,
  setState,
  disabled,
}: {
  s: Season
  state: WeekState
  setState: (w: WeekState) => void
  disabled: boolean
}) {
  const [adding, setAdding] = useState<number | null>(null)
  const [drop, setDrop] = useState('')
  const [from, setFrom] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [shown, setShown] = useState(10)
  const all = freeAgents(s, state, 60)
  const pool = all.slice(0, shown)
  const left = MAX_ADDS - state.moves.length
  const teams = teamNames(s)
  const busiest = [...teamGamesInWeek(s, state.days).entries()].sort(
    (a, b) => b[1] - a[1] || (teams.get(a[0]) ?? '').localeCompare(teams.get(b[0]) ?? ''),
  )
  const roster = rosterOn(state, state.days.length)
  const name = (pid: number) => s.players.get(pid)?.name ?? `Player ${pid}`
  const confirm = (add: number) => {
    const r = addPlayer(state, from - 1, add, Number(drop))
    setError(r.error)
    if (!r.error) {
      setState(r.state)
      setAdding(null)
    }
  }
  return (
    <Section title="Waivers">
      <p className="text-subhead">
        <span className="font-semibold tabular-nums">
          {left} of {MAX_ADDS}
        </span>{' '}
        adds left this week. A pickup plays from the day you choose.
      </p>
      {busiest.length > 0 && (
        <p className="text-caption text-muted">
          Games by NBA team this week:{' '}
          {busiest.map(([t, n]) => `${teams.get(t) ?? t} ${n}`).join(' · ')}
        </p>
      )}
      {state.moves.length > 0 && (
        <ul aria-label="Your pickups this week" className="flex flex-col gap-1 text-subhead">
          {state.moves.map((m, i) => (
            <li key={`${m.add}-${m.drop}`} className="flex items-center justify-between gap-2">
              <span>
                + {name(m.add)} for − {name(m.drop)}, from{' '}
                {dayLabel(state.days[m.madeOn + 1] ?? state.days[0] ?? '')}
              </span>
              {i === state.moves.length - 1 && !disabled && (
                <Button
                  variant="secondary"
                  onClick={() => setState({ ...state, moves: state.moves.slice(0, -1) })}
                >
                  Undo
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <ul aria-label="Free agents" className="flex flex-col divide-y divide-line">
        {pool.map(({ player: p, games }) => (
          <li key={p.id} className="flex flex-col gap-2 py-2">
            <div className="flex items-center gap-3">
              <span className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-body font-semibold">{p.name}</span>
                <span className="truncate text-caption text-muted">
                  {[p.team, p.pos ?? 'Util'].filter(Boolean).join(' · ')} · value $
                  {Math.round(p.usd)}
                </span>
              </span>
              <span className="text-subhead whitespace-nowrap tabular-nums">
                {games} {games === 1 ? 'game' : 'games'}
              </span>
              <Button
                variant="secondary"
                disabled={disabled || left <= 0}
                aria-label={`Add ${p.name}`}
                onClick={() => {
                  setAdding(p.id)
                  // default: your least valuable player
                  const weakest = [...roster].sort(
                    (a, b) => (s.players.get(a)?.usd ?? 0) - (s.players.get(b)?.usd ?? 0),
                  )[0]
                  setDrop(String(weakest ?? ''))
                  setFrom(0)
                  setError(null)
                }}
              >
                Add
              </Button>
            </div>
            {adding === p.id && (
              <div
                role="group"
                aria-label={`Pick up ${p.name}`}
                className="flex flex-wrap items-end gap-2"
              >
                <label className={cx(label, 'min-w-[180px] flex-1')}>
                  Drop
                  <select className={select} value={drop} onChange={(e) => setDrop(e.target.value)}>
                    {roster.map((pid) => (
                      <option key={pid} value={pid}>
                        {name(pid)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className={cx(label, 'min-w-[140px]')}>
                  Plays from
                  <select
                    className={select}
                    value={from}
                    onChange={(e) => setFrom(Number(e.target.value))}
                  >
                    {state.days.map((d, i) => (
                      <option key={d} value={i}>
                        {dayLabel(d)}
                      </option>
                    ))}
                  </select>
                </label>
                <Button onClick={() => confirm(p.id)}>Confirm</Button>
                <Button variant="secondary" onClick={() => setAdding(null)}>
                  Cancel
                </Button>
              </div>
            )}
          </li>
        ))}
      </ul>
      {all.length > shown && (
        <Button variant="secondary" onClick={() => setShown(shown + 15)}>
          Show more free agents
        </Button>
      )}
      {left <= 0 && (
        <p className="text-caption text-muted">
          You&apos;ve used all {MAX_ADDS} adds this week: Add is off until next week.
        </p>
      )}
      {error && (
        <p role="alert" className="text-subhead text-lose">
          {error}
        </p>
      )}
    </Section>
  )
}

function Result({
  s,
  state,
  result,
  kept,
  onKeep,
  onBack,
}: {
  s: Season
  state: WeekState
  result: WeekResult
  kept: boolean
  onKeep: () => void
  onBack: () => void
}) {
  const r = result.record
  const verdict = r.wins > r.losses ? 'Won' : r.wins < r.losses ? 'Lost' : 'Tied'
  const name = (pid: number) => s.players.get(pid)?.name ?? `Player ${pid}`
  return (
    <Section title="This week, as it happened">
      <p className="text-display font-semibold tabular-nums">
        {verdict} {recordText(r)}
      </p>
      <CategoryTable rows={result.categories} caption="Category results" />
      <h3 className="text-caption font-semibold tracking-eyebrow text-muted uppercase">
        Day by day
      </h3>
      <ol aria-label="Day by day" className="flex flex-col gap-2">
        {result.days.map((d) => {
          const today = s.lines.get(d.day)
          const pts = (ids: number[]) => ids.reduce((n, id) => n + (today?.get(id)?.pts ?? 0), 0)
          return (
            <li key={d.day} className="flex flex-col gap-0.5 text-subhead">
              <span className="font-semibold">
                {dayLabel(d.day)} · {pts(d.mine)} pts vs {pts(d.theirs)}
              </span>
              {d.mine.length > 0 ? (
                <span className="text-ink-2">
                  {d.mine
                    .map((id) => {
                      const l = today?.get(id)
                      return l ? `${name(id)} ${l.pts}/${l.reb}/${l.ast}` : `${name(id)} DNP`
                    })
                    .join(' · ')}
                </span>
              ) : (
                <span className="text-muted">No starters with a game</span>
              )}
            </li>
          )
        })}
      </ol>
      <p className="text-caption text-muted">
        Lines are points/rebounds/assists. DNP: didn&apos;t play.
      </p>
      <div className="flex flex-wrap gap-2">
        {!kept && <Button onClick={onKeep}>Keep this result</Button>}
        <Button variant="secondary" onClick={onBack}>
          Change lineup or pickups
        </Button>
      </div>
      {state.moves.length > 0 && !kept && (
        <p className="text-caption text-muted">Keeping it also keeps this week&apos;s pickups.</p>
      )}
    </Section>
  )
}
