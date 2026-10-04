// DRAFT-014: practise the auction against 15 simulated managers, with the draft-night advice.
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { usePlayers, useReplayLoader, useReplaySeasons, useSimsApi } from '../../api/client'
import { enqueue, flush, runSim, syncLeague } from '../sims/sync'
import type { PlayerRow } from '../../api/types'
import { Avatar } from '../../components/ui/Avatar'
import { Button, ButtonLink } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { PageHeader } from '../../components/ui/PageHeader'
import { QueryState } from '../../components/ui/QueryState'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { PlayerBadgeChip } from '../players/PlayerBadges'
import { badgesOf } from '../players/badges'
import { CATEGORIES, fold, headshotUrl } from '../players/format'
import { leagueFromSales, loadLeague, saveLeague } from '../replay/league'
import { REPLAY_SEASONS, draftPool, parseSeason, type ReplayDoc } from '../replay/season'
import { replayRows } from '../replay/rows'
import { audioPort } from './fx/audio'
import { ClockRing } from './fx/ClockRing'
import { cuesFor, tickCue } from './fx/cues'
import { SoundControls } from './fx/SoundControls'
import { useFx, type Fx } from './fx/useFx'
import { teamState, type Advice, type DraftPlayer } from './live'
import {
  BID_SECONDS,
  ME,
  NOMINATE_SECONDS,
  TEAMS,
  bid,
  bidExpired,
  clearSave,
  fastForward,
  fitLine,
  loadSave,
  myAdvice,
  myState,
  needs,
  nominate,
  nominateExpired,
  pass,
  resume,
  save,
  start,
  toDraftPlayers,
  undoLast,
  verdict,
  type Pace,
  type Practice,
  type Settings,
  type Verdict,
} from './practice'
import { addToHistory, buildReport, type Report } from './report'
import { ReportView, signed, type SavedReport } from './ReportView'
import { STYLES, STYLE_LABEL, type Style } from './room'

const field = 'surface rounded-chip text-ink focus-visible:outline-2 focus-visible:outline-accent'
const select = cx(field, INTERACTIVE, 'min-h-11 w-full px-2.5 text-subhead')
const label = 'flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase'
const newSeed = () => Math.floor(Math.random() * 1_000_000_000)

export function DraftPracticePage() {
  const q = usePlayers('all')
  return (
    <QueryState
      q={q}
      notReady={{
        title: 'Draft practice needs player values',
        body: 'It opens once the pre-season projection run publishes auction values.',
      }}
    >
      {(data) => <Practice rows={data.players} />}
    </QueryState>
  )
}

type Pool = { players: DraftPlayer[]; names: Map<string, PlayerRow> }

function Practice({ rows }: { rows: PlayerRow[] }) {
  const current: Pool = useMemo(
    () => ({
      players: toDraftPlayers(rows),
      names: new Map(rows.map((r) => [String(r.id), r])),
    }),
    [rows],
  )
  const [practice, setPractice] = useState<Practice | null>(null)
  const [saved, setSaved] = useState(loadSave)
  // SIM-002: a replay draft runs on that season's pool, loaded when it starts (or resumes).
  const [replay, setReplay] = useState<Pool | null>(null)
  const [loading, setLoading] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const loadReplay = useReplayLoader()
  const pool = practice?.settings.season ? (replay ?? current) : current
  const { players, names } = pool

  const withPool = async (settings: Settings, then: (p: Pool) => void) => {
    if (!settings.season) return then(current)
    setLoading(settings.season)
    setLoadError(null)
    try {
      const season = parseSeason((await loadReplay(settings.season)) as ReplayDoc)
      const next = { players: draftPool(season), names: replayRows(season) }
      if (next.players.length < TEAMS.length * 14)
        throw new Error(
          `the ${settings.season} file has only ${next.players.length} valued players`,
        )
      setReplay(next)
      then(next)
    } catch (e) {
      setLoadError(
        `Couldn't load the ${settings.season} season (${e instanceof Error ? e.message : 'error'}). Try again, or practise this season.`,
      )
    } finally {
      setLoading(null)
    }
  }

  useEffect(() => {
    if (!practice) return
    if (practice.phase === 'done') clearSave()
    else save(practice)
  }, [practice])

  if (players.length < TEAMS.length * 14)
    return (
      <div className="mx-auto flex w-full max-w-[640px] flex-col gap-4 px-5 pt-5 pb-8 min-[840px]:pt-8">
        <PageHeader title="Draft practice" trailing={<SampleBadge />} />
        <Card className="flex flex-col gap-2 p-4">
          <p className="text-headline">Practice needs the full player pool</p>
          <p className="text-body text-ink-2">
            A practice auction sells {TEAMS.length * 14} players, and only {players.length} are
            loaded. Sign in to practise with this season&apos;s published values.
          </p>
        </Card>
      </div>
    )
  if (!practice)
    return (
      <Setup
        saved={saved ? saved.sales.length : null}
        savedSeason={saved?.settings.season ?? null}
        loading={loading}
        error={loadError}
        onStart={(s) => {
          void audioPort().unlock()
          const settings = { ...s, startedAt: new Date().toISOString() }
          void withPool(settings, (p) => setPractice(start(p.players, settings)))
        }}
        onResume={() => {
          void audioPort().unlock()
          if (saved) void withPool(saved.settings, (p) => setPractice(resume(p.players, saved)))
        }}
        onDiscard={() => {
          clearSave()
          setSaved(null)
        }}
      />
    )
  return (
    <Room
      practice={practice}
      setPractice={setPractice}
      names={names}
      onQuit={() => {
        clearSave()
        setSaved(null)
        setPractice(null)
      }}
      onAgain={(sameRoom) => {
        void audioPort().unlock()
        setPractice(
          start(players, {
            ...practice.settings,
            seed: sameRoom ? practice.settings.seed : newSeed(),
            startedAt: new Date().toISOString(),
          }),
        )
      }}
    />
  )
}

// --- setup ---------------------------------------------------------------------------------------

function Setup({
  saved,
  savedSeason,
  loading,
  error,
  onStart,
  onResume,
  onDiscard,
}: {
  saved: number | null
  savedSeason: string | null
  loading: string | null
  error: string | null
  onStart: (s: Settings) => void
  onResume: () => void
  onDiscard: () => void
}) {
  const [punted, setPunted] = useState<string>('none')
  const [styles, setStyles] = useState<'mix' | Style>('mix')
  const [pace, setPace] = useState<Pace>('real')
  const [season, setSeason] = useState<string>('current')
  const published = new Set(useReplaySeasons().data?.seasons ?? [])
  return (
    <div className="mx-auto flex w-full max-w-[640px] flex-col gap-5 px-5 pt-5 pb-8 min-[840px]:pt-8">
      <PageHeader title="Draft practice" trailing={<SampleBadge />} />
      <p className="-mt-2 text-body text-ink-2">
        A full auction against 15 simulated managers: $200 each, 14 spots, 224 sales. You get the
        same advice as the draft-night board: your max bid, a ceiling for every player, targets and
        nomination ideas.
      </p>
      {saved !== null && (
        <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
          <p className="text-body">
            An unfinished {savedSeason ? `${savedSeason} replay` : 'practice'} draft:{' '}
            <span className="tabular-nums">{saved}</span> of 224 sold.
          </p>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={onDiscard}>
              Discard
            </Button>
            <Button onClick={onResume}>Resume</Button>
          </div>
        </Card>
      )}
      <Card className="flex flex-col gap-4 p-4">
        <label className={label}>
          Season
          <select
            className={select}
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            aria-describedby="season-hint"
          >
            <option value="current">This season (2026-27)</option>
            {REPLAY_SEASONS.map((s) => (
              <option key={s} value={s} disabled={!published.has(s)}>
                Replay {s}
                {published.has(s) ? '' : ' (not published yet)'}
              </option>
            ))}
          </select>
        </label>
        <p id="season-hint" className="-mt-2 text-caption text-muted">
          {season === 'current'
            ? 'A past season drafts on the values as they stood before it began; afterwards you can play that season week by week.'
            : `Values as they stood before ${season} began. Afterwards, play the season week by week on the real box scores.`}
          {published.size < REPLAY_SEASONS.length &&
            ' Seasons not published yet appear after the next daily update.'}
        </p>
        <label className={label}>
          Your strategy
          <select className={select} value={punted} onChange={(e) => setPunted(e.target.value)}>
            <option value="none">All categories</option>
            {CATEGORIES.map(([k, l], i) => (
              <option key={k} value={String(i)}>
                Punt {l}
              </option>
            ))}
          </select>
        </label>
        <label className={label}>
          Opponents
          <select
            className={select}
            value={styles}
            onChange={(e) => setStyles(e.target.value as 'mix' | Style)}
          >
            <option value="mix">A mix of styles</option>
            {STYLES.map((s) => (
              <option key={s} value={s}>
                All {STYLE_LABEL[s].toLowerCase()}
              </option>
            ))}
          </select>
        </label>
        <fieldset className="flex flex-col gap-2">
          <legend className="pb-1 text-caption tracking-eyebrow text-muted uppercase">Pace</legend>
          {(
            [
              ['real', 'Real timers', '30 s to nominate, 20 s to bid, like draft night'],
              ['untimed', 'Untimed', 'Take as long as you like'],
            ] as const
          ).map(([v, t, d]) => (
            <label key={v} className="flex min-h-11 cursor-pointer items-center gap-3 text-body">
              <input
                type="radio"
                name="pace"
                value={v}
                checked={pace === v}
                onChange={() => setPace(v)}
                className="size-4 accent-[var(--accent)]"
              />
              <span>
                {t} <span className="text-subhead text-muted">· {d}</span>
              </span>
            </label>
          ))}
        </fieldset>
        <Button
          onClick={() =>
            onStart({
              seed: newSeed(),
              styles,
              punted: punted === 'none' ? null : Number(punted),
              pace,
              ...(season === 'current' ? {} : { season }),
            })
          }
          disabled={loading !== null}
        >
          {loading ? `Loading ${loading}…` : 'Start practice draft'}
        </Button>
        {error && (
          <p role="alert" className="text-subhead text-lose">
            {error}
          </p>
        )}
      </Card>
      <p className="text-caption text-muted">
        The other managers are simulated, not your league&apos;s real managers: they bid around the
        published values with different styles. Signed in, finished drafts are kept with your
        account.
      </p>
      <nav aria-label="Practice tools" className="flex flex-wrap gap-2">
        <ButtonLink to="/sims">Past sims</ButtonLink>
        <ButtonLink to="/replay">Season replay</ButtonLink>
      </nav>
    </div>
  )
}

// --- the room ------------------------------------------------------------------------------------

/** The lot's clock; remounted (by `key`) for every lot and bid, so it always starts full. */
function Countdown({
  seconds,
  label,
  fx,
  onExpire,
}: {
  seconds: number
  label: string
  fx: Fx
  onExpire: () => void
}) {
  const [end] = useState(() => Date.now() + seconds * 1000)
  const [left, setLeft] = useState(seconds)
  const expire = useRef(onExpire)
  const sound = useRef(fx)
  useEffect(() => {
    expire.current = onExpire
    sound.current = fx
  })
  useEffect(() => {
    let lastHalf = seconds * 2
    const id = setInterval(() => {
      const ms = Math.max(0, end - Date.now())
      const s = Math.ceil(ms / 1000)
      const half = Math.ceil(ms / 500)
      setLeft(s)
      // A tick per half-second boundary; after a long gap (a hidden tab) only the true value counts.
      if (half < lastHalf) {
        const cue = lastHalf - half <= 2 ? tickCue(half, sound.current.prefs.tick) : null
        if (cue) sound.current.play(cue)
        lastHalf = half
      }
      if (s === 0) {
        clearInterval(id)
        sound.current.play('expire')
        expire.current()
      }
    }, 250)
    return () => clearInterval(id)
  }, [end, seconds])
  return <Timer left={left} total={seconds} end={end} label={label} reduced={fx.reduced} />
}

function Room({
  practice: p,
  setPractice,
  names,
  onQuit,
  onAgain,
}: {
  practice: Practice
  setPractice: (p: Practice) => void
  names: Map<string, PlayerRow>
  onQuit: () => void
  onAgain: (sameRoom: boolean) => void
}) {
  const [error, setError] = useState<string | null>(null)
  const fx = useFx()
  const [sold, setSold] = useState<{ pid: string; team: string; price: number } | null>(null)
  const before = useRef(p)
  const quiet = useRef(false)
  const advice = useMemo(() => myAdvice(p), [p])
  const fit = useMemo(() => makeFit(p, advice), [p, advice])
  const me = myState(p)
  const timed = p.settings.pace === 'real' && p.phase !== 'done'
  const lotKey =
    p.phase === 'lot' && p.lot
      ? `${p.room.sales.length}-${p.lot.price}-${p.lot.high}`
      : `${p.room.sales.length}-nominate`
  const timer = timed ? (
    <Countdown
      key={lotKey}
      fx={fx}
      label={p.phase === 'nominate' ? 'to nominate' : 'to bid'}
      seconds={p.phase === 'nominate' ? NOMINATE_SECONDS : BID_SECONDS}
      onExpire={() => setPractice(p.phase === 'nominate' ? nominateExpired(p) : bidExpired(p))}
    />
  ) : null

  // Sounds and the "sold" stamp follow what changed between two states; fast-forward stays quiet.
  const { playAll } = fx
  useEffect(() => {
    const prev = before.current
    before.current = p
    if (prev === p) return
    const ff = quiet.current
    quiet.current = false
    playAll(cuesFor(prev, p, { fastForward: ff }))
    const sale = p.room.sales[prev.room.sales.length]
    setSold(!ff && sale && p.room.sales.length > prev.room.sales.length ? sale : null)
  }, [p, playAll])
  // Walking in on an open lot (a rival nominated first) gets the same cue as a lot opening later.
  useEffect(() => {
    if (before.current.phase === 'lot') playAll(['nominate'])
  }, [playAll])
  useEffect(() => {
    if (!sold) return
    const id = setTimeout(() => setSold(null), 1800)
    return () => clearTimeout(id)
  }, [sold])
  const fastForwardTo = (untilMine: boolean) => {
    quiet.current = true
    setPractice(fastForward(p, untilMine))
  }

  const doBid = (amount: number) => {
    const r = bid(p, amount)
    setError(r.error)
    if (!r.error) setPractice(r.practice)
  }
  const doPass = () => {
    setError(null)
    setPractice(pass(p))
  }

  // B = +$1, Shift+B = +$5, P = pass (not while typing). One listener; it reads the latest handlers.
  const keys = useRef<(e: KeyboardEvent) => void>(() => {})
  useEffect(() => {
    keys.current = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return
      if (p.phase !== 'lot' || !p.lot) return
      if (e.key === 'b') doBid(p.lot.price + 1)
      else if (e.key === 'B') doBid(p.lot.price + 5)
      else if (e.key === 'p' || e.key === 'P') doPass()
    }
  })
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => keys.current(e)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (p.phase === 'done')
    return <Done practice={p} names={names} onAgain={onAgain} onQuit={onQuit} />

  const soldCount = p.room.sales.length
  const motion = !fx.reduced
  return (
    <div className="flex flex-col gap-4 px-5 pt-5 pb-8 min-[840px]:px-0 min-[840px]:pt-8">
      <PageHeader
        eyebrow={`${p.settings.season ? `${p.settings.season} replay · ` : ''}Sale ${soldCount + 1} of 224`}
        title="Draft practice"
        trailing={<SampleBadge />}
      />
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-subhead">
        <Stat label="Budget left" value={`$${me.left}`} />
        <Stat label="Max bid" value={`$${me.max_bid}`} />
        <Stat label="Open spots" value={String(me.open)} />
      </div>
      <SoundControls fx={fx} />
      {sold && (
        <p
          aria-hidden="true"
          data-testid="sold-stamp"
          className={cx(
            'pointer-events-none fixed inset-x-5 top-20 z-30 mx-auto w-fit max-w-[calc(100%-2.5rem)] rounded-chip border-2 border-ink-2 bg-surface px-3 py-1 text-center text-headline font-bold tracking-eyebrow text-ink-2 uppercase',
            motion && 'sold-stamp',
          )}
        >
          Sold · {names.get(sold.pid)?.name ?? sold.pid} · {sold.team === ME ? 'you' : sold.team} ·
          ${sold.price}
        </p>
      )}

      {/* Reading order = visual order: the lot, its controls and recommendations; then needs, team, rivals. */}
      <div className="grid items-start gap-4 min-[1100px]:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex flex-col gap-4">
          {p.phase === 'nominate' ? (
            <Nominate
              motion={motion}
              practice={p}
              fit={fit}
              names={names}
              timer={timer}
              onNominate={(pid) => {
                setError(null)
                setPractice(nominate(p, pid))
              }}
            />
          ) : (
            p.lot && (
              <LotCard
                key={p.lot.pid}
                motion={motion}
                practice={p}
                fit={fit}
                names={names}
                row={names.get(p.lot.pid)}
                ceiling={advice.players[p.lot.pid]?.ceiling ?? 0}
                maxBid={me.max_bid}
                timer={timer}
                error={error}
                onBid={doBid}
                onPass={doPass}
              />
            )
          )}
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                onClick={() => setPractice(undoLast(p))}
                disabled={p.undo.length === 0}
              >
                Undo
              </Button>
              <Button variant="secondary" onClick={() => fastForwardTo(true)}>
                Sim to my next nomination
              </Button>
              <Button variant="secondary" onClick={() => fastForwardTo(false)}>
                Sim the rest
              </Button>
              <Button variant="secondary" onClick={onQuit}>
                Quit
              </Button>
            </div>
            <p className="text-caption text-muted">
              Fast-forward bids for you up to the helper&apos;s ceilings.
            </p>
          </div>
          {p.phase === 'lot' && (
            <Recommended practice={p} fit={fit} names={names} exclude={p.lot?.pid ?? null} />
          )}
        </div>
        <div className="flex flex-col gap-4">
          <Needs practice={p} fit={fit} />
          <MyTeam practice={p} names={names} />
          <Rivals practice={p} names={names} />
          <RecentSales practice={p} names={names} />
        </div>
      </div>
    </div>
  )
}

function Stat({ label: l, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="text-caption tracking-eyebrow text-muted uppercase">{l}</span>
      <span className="text-headline font-semibold tabular-nums">{value}</span>
    </span>
  )
}

function Timer({
  left,
  total,
  end,
  label,
  reduced,
}: {
  left: number
  total: number
  end: number
  label: string
  reduced: boolean
}) {
  const say = left === 10 || left === 5 ? `${left} seconds left` : ''
  return (
    <div className="flex items-center gap-3">
      <ClockRing end={end} total={total} left={left} reduced={reduced} />
      <span className="text-subhead text-ink-2">{label}</span>
      <span aria-live="polite" className="sr-only">
        {say}
      </span>
    </div>
  )
}

/** A labelled panel (a named region for screen readers and tests). */
function Section({
  title,
  className,
  children,
}: {
  title: string
  className?: string
  children: ReactNode
}) {
  const id = useId()
  return (
    <section aria-labelledby={id} className={className}>
      <Card className="flex flex-col gap-3 p-4">
        <h2 id={id} className="text-caption font-semibold tracking-eyebrow text-muted uppercase">
          {title}
        </h2>
        {children}
      </Card>
    </section>
  )
}

/** A player's headshot (initials when it can't load); decorative. */
function Face({ pid, names, size }: { pid: string; names: Map<string, PlayerRow>; size: number }) {
  const row = names.get(pid)
  return <Avatar src={headshotUrl(Number(pid))} name={row?.name ?? pid} size={size} />
}

/** The engine's advice for one state, computed once per render (DRAFT-016 review) and shared. */
type Fit = { advice: Advice; line: (pid: string) => string }

function makeFit(p: Practice, advice: Advice): Fit {
  const z = new Map(p.room.players.map((x) => [x.id, x.z]))
  return {
    advice,
    line: (pid: string) =>
      fitLine(z.get(pid) ?? [], advice.weights, advice.players[pid]?.fit ?? 1, p.settings.punted),
  }
}

/** One recommended player: face, name, why, ceiling. A button when it can be nominated. */
function PickRow({
  pid,
  names,
  why,
  ceiling,
  onPick,
}: {
  pid: string
  names: Map<string, PlayerRow>
  why: string
  ceiling: number | undefined
  onPick?: () => void
}) {
  const r = names.get(pid)
  const body = (
    <>
      <Face pid={pid} names={names} size={36} />
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-body font-semibold">{r?.name ?? pid}</span>
        <span className="truncate text-caption text-ink-2">{why}</span>
      </span>
      <span className="flex flex-col items-end text-subhead tabular-nums">
        {ceiling !== undefined && <span className="font-semibold">up to ${ceiling}</span>}
        <span className="text-caption text-muted">value ${Math.round(r?.dollars ?? 0)}</span>
      </span>
    </>
  )
  const cls = 'flex min-h-11 w-full items-center gap-3 rounded-row px-2 py-1.5 text-left'
  return (
    <li>
      {onPick ? (
        <button
          type="button"
          onClick={onPick}
          className={cx(INTERACTIVE, 'press hover:bg-surface-2', cls)}
        >
          {body}
        </button>
      ) : (
        <div className={cls}>{body}</div>
      )}
    </li>
  )
}

function Nominate({
  motion,
  practice: p,
  fit,
  names,
  timer,
  onNominate,
}: {
  motion: boolean
  practice: Practice
  fit: Fit
  names: Map<string, PlayerRow>
  timer: ReactNode
  onNominate: (pid: string) => void
}) {
  const [query, setQuery] = useState('')
  const { advice, line } = fit
  const taken = new Set(p.room.sales.map((s) => s.pid))
  const needle = fold(query.trim())
  const matches =
    needle.length < 2
      ? []
      : [...names.values()]
          .filter((r) => !taken.has(String(r.id)) && fold(r.name).includes(needle))
          .slice(0, 8)
  return (
    <Section title="Your nomination" className={motion ? 'lot-in' : undefined}>
      {timer}
      <input
        type="search"
        aria-label="Search players to nominate"
        placeholder="Search players to nominate"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className={cx(field, 'min-h-11 w-full px-3 text-body placeholder:text-muted')}
      />
      {matches.length > 0 && (
        <ul aria-label="Search results" className="flex flex-col">
          {matches.map((r) => (
            <PickRow
              key={r.id}
              pid={String(r.id)}
              names={names}
              why={line(String(r.id))}
              ceiling={advice.players[String(r.id)]?.ceiling}
              onPick={() => onNominate(String(r.id))}
            />
          ))}
        </ul>
      )}
      <div className="grid gap-4 min-[600px]:grid-cols-2">
        <div className="flex flex-col gap-1">
          <h3 className="text-subhead font-semibold">Nominate a target</h3>
          <ul aria-label="Your targets" className="flex flex-col">
            {advice.targets.slice(0, 5).map((pid) => (
              <PickRow
                key={pid}
                pid={pid}
                names={names}
                why={line(pid)}
                ceiling={advice.players[pid]?.ceiling}
                onPick={() => onNominate(pid)}
              />
            ))}
          </ul>
        </div>
        {advice.hints.length > 0 && (
          <div className="flex flex-col gap-1">
            <h3 className="text-subhead font-semibold">Or drain a rival&apos;s budget</h3>
            <ul aria-label="Nomination ideas" className="flex flex-col">
              {advice.hints.slice(0, 3).map((pid) => (
                <PickRow
                  key={pid}
                  pid={pid}
                  names={names}
                  why="Others value him more than you do"
                  ceiling={advice.players[pid]?.ceiling}
                  onPick={() => onNominate(pid)}
                />
              ))}
            </ul>
          </div>
        )}
      </div>
      {timer !== null && (
        <p className="text-caption text-muted">When time runs out, your top target is nominated.</p>
      )}
    </Section>
  )
}

const VERDICT: Record<Verdict, { text: (c: number) => string; tone: string }> = {
  good: { text: (c) => `Good buy: bid up to $${c}`, tone: 'bg-win/12 text-win' },
  near: { text: (c) => `Near your limit: up to $${c}`, tone: 'bg-warn/12 text-warn' },
  pass: { text: (c) => `Pass: over your $${c} ceiling`, tone: 'bg-surface-2 text-ink-2' },
  cant: { text: () => "You can't bid on him", tone: 'bg-surface-2 text-ink-2' },
}

function LotCard({
  motion,
  practice: p,
  fit,
  names,
  row,
  ceiling,
  maxBid,
  timer,
  error,
  onBid,
  onPass,
}: {
  motion: boolean
  practice: Practice
  fit: Fit
  names: Map<string, PlayerRow>
  row: PlayerRow | undefined
  ceiling: number
  maxBid: number
  timer: ReactNode
  error: string | null
  onBid: (amount: number) => void
  onPass: () => void
}) {
  const lot = p.lot
  const [custom, setCustom] = useState('')
  const { advice, line } = fit
  if (!lot) return null
  const mine = lot.high === ME
  const nominatedBy = lot.nominatedBy === ME ? 'you' : lot.nominatedBy
  const state = verdict(lot.price, ceiling, myState(p).open > 0 && maxBid > lot.price)
  const v = VERDICT[state]
  const next = advice.targets.find((pid) => pid !== lot.pid)
  const badges = row ? badgesOf(row).slice(0, 3) : []
  return (
    <Section
      title={`On the block · nominated by ${nominatedBy}`}
      className={motion ? 'lot-in' : undefined}
    >
      <div className="flex items-start gap-3">
        <Face pid={lot.pid} names={names} size={64} />
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <p className="text-title">{row?.name ?? lot.pid}</p>
          <p className="text-subhead text-muted">
            {[row?.team, row?.positions].filter(Boolean).join(' · ')} · value $
            {Math.round(row?.dollars ?? 0)}
          </p>
          {badges.length > 0 && (
            <div className="flex flex-wrap gap-1" data-testid="lot-badges">
              {badges.map((b) => (
                <PlayerBadgeChip key={b.code} badge={b} />
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 flex-col items-end">
          <p className="text-caption tracking-eyebrow text-muted uppercase">Current bid</p>
          <p className="text-title-lg tabular-nums" aria-live="polite">
            <span key={lot.price} className={cx('inline-block', motion && 'price-pop')}>
              ${lot.price}
            </span>
          </p>
          <p key={lot.high} className={cx('text-subhead text-ink-2', motion && 'bidder-flash')}>
            {mine ? 'You' : lot.high}
          </p>
        </div>
      </div>
      {timer}
      <div
        className={cx('flex flex-col gap-0.5 rounded-row px-3 py-2.5', v.tone)}
        data-testid="verdict"
      >
        <p className="text-headline font-semibold">{v.text(ceiling)}</p>
        <p className="text-subhead">{line(lot.pid)}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => onBid(lot.price + 1)} aria-keyshortcuts="b">
          Bid ${lot.price + 1}
        </Button>
        <Button
          variant="secondary"
          onClick={() => onBid(lot.price + 5)}
          aria-keyshortcuts="Shift+B"
        >
          Bid ${lot.price + 5}
        </Button>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            onBid(Number(custom))
            setCustom('')
          }}
        >
          <input
            inputMode="numeric"
            aria-label="Custom bid in dollars"
            placeholder="$"
            value={custom}
            onChange={(e) => setCustom(e.target.value.replace(/\D/g, ''))}
            className={cx(field, 'min-h-11 w-20 px-3 text-body tabular-nums')}
          />
          <Button type="submit" variant="secondary">
            Bid
          </Button>
        </form>
        <Button variant="secondary" onClick={onPass} aria-keyshortcuts="p" className="ml-auto">
          Pass
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-subhead text-lose">
          {error}
        </p>
      )}
      <p className="text-caption text-ink-2" data-testid="if-you-pass">
        {myState(p).open === 0
          ? "You're done buying: your roster is full."
          : next
            ? `If you pass: next best is ${names.get(next)?.name ?? next}, up to $${advice.players[next]?.ceiling ?? 0}.`
            : 'No other targets left.'}
      </p>
      <p className="hidden text-caption text-muted min-[840px]:block">
        Your max bid: ${maxBid}. Keys: B bids +$1, Shift+B +$5, P passes.
      </p>
    </Section>
  )
}

/** Your neediest and best-covered categories right now (the engine's live weights). */
function Needs({ practice: p, fit }: { practice: Practice; fit: Fit }) {
  const n = needs(fit.advice.weights, p.settings.punted)
  return (
    <Section title="Your needs">
      {n.need.length === 0 && n.covered.length === 0 ? (
        <p className="text-subhead text-muted">Draft anyone: no needs yet.</p>
      ) : (
        <dl className="grid grid-cols-[auto_1fr] items-baseline gap-x-3 gap-y-1.5 text-subhead">
          <dt className="text-caption text-muted">Need</dt>
          <dd className="font-semibold" data-testid="needs">
            {n.need.map((c) => c.label).join(' · ') || 'Nothing urgent'}
          </dd>
          <dt className="text-caption text-muted">Covered</dt>
          <dd className="text-ink-2">{n.covered.map((c) => c.label).join(' · ') || '—'}</dd>
        </dl>
      )}
      {n.punted && <p className="text-caption text-muted">Punted: {n.punted}</p>}
    </Section>
  )
}

/** The top available targets for your roster, on every lot (DRAFT-016 AC5). */
function Recommended({
  practice: p,
  fit,
  names,
  exclude,
  onNominate,
}: {
  practice: Practice
  fit: Fit
  names: Map<string, PlayerRow>
  exclude: string | null
  onNominate?: (pid: string) => void
}) {
  const { advice, line } = fit
  const top = advice.targets.filter((pid) => pid !== exclude).slice(0, 5)
  return (
    <Section title="Recommended for you">
      {myState(p).open === 0 ? (
        <p className="text-subhead text-muted">You&apos;re done buying.</p>
      ) : (
        <ul aria-label="Recommended for you" className="flex flex-col">
          {top.map((pid) => (
            <PickRow
              key={pid}
              pid={pid}
              names={names}
              why={line(pid)}
              ceiling={advice.players[pid]?.ceiling}
              onPick={onNominate ? () => onNominate(pid) : undefined}
            />
          ))}
        </ul>
      )}
    </Section>
  )
}

function SaleRow({
  pid,
  names,
  price,
  note,
}: {
  pid: string
  names: Map<string, PlayerRow>
  price: number
  note?: string
}) {
  return (
    <li className="flex items-center gap-2.5 py-1.5 text-subhead">
      <Face pid={pid} names={names} size={28} />
      <span className="min-w-0 flex-1 truncate">
        {names.get(pid)?.name ?? pid}
        {note && <span className="text-muted"> → {note}</span>}
      </span>
      <span className="tabular-nums">${price}</span>
    </li>
  )
}

function MyTeam({ practice: p, names }: { practice: Practice; names: Map<string, PlayerRow> }) {
  const mine = p.room.sales.filter((s) => s.team === ME)
  return (
    <Section title={`Your team · ${mine.length} of 14`}>
      {mine.length === 0 ? (
        <p className="text-subhead text-muted">No players yet.</p>
      ) : (
        <ul aria-label="Your team" className="flex flex-col divide-y divide-line">
          {mine.map((s) => (
            <SaleRow key={s.pid} pid={s.pid} names={names} price={s.price} />
          ))}
        </ul>
      )}
    </Section>
  )
}

/** Every rival's money, and their roster on demand (DRAFT-016 AC6). */
function Rivals({ practice: p, names }: { practice: Practice; names: Map<string, PlayerRow> }) {
  const [open, setOpen] = useState<string | null>(null)
  const state = teamState(p.room.sales, p.room.teams, p.room.budget, p.room.slots)
  return (
    <Section title="Rivals">
      <ul aria-label="Rivals" className="flex flex-col divide-y divide-line">
        {p.room.teams
          .filter((t) => t !== ME)
          .map((t) => {
            const s = state[t]
            const roster = p.room.sales.filter((x) => x.team === t)
            const expanded = open === t
            return (
              <li key={t} className="py-0.5">
                <button
                  type="button"
                  aria-expanded={expanded}
                  onClick={() => setOpen(expanded ? null : t)}
                  className={cx(
                    INTERACTIVE,
                    'press flex min-h-11 w-full items-center gap-2 rounded-row px-1 text-left text-subhead hover:bg-surface-2',
                    s?.open === 0 && 'text-muted',
                  )}
                >
                  <span className="flex-1 font-medium">{t}</span>
                  <span className="tabular-nums">${s?.left} left</span>
                  <span className="w-14 text-right text-caption text-muted tabular-nums">
                    {s?.open} spots
                  </span>
                  <span aria-hidden="true" className="w-3 text-muted">
                    {expanded ? '−' : '+'}
                  </span>
                </button>
                {expanded && (
                  <div className="reveal px-1 pb-2">
                    {roster.length === 0 ? (
                      <p className="text-caption text-muted">No players yet.</p>
                    ) : (
                      <ul aria-label={`${t} roster`} className="flex flex-col">
                        {roster.map((x) => (
                          <SaleRow key={x.pid} pid={x.pid} names={names} price={x.price} />
                        ))}
                      </ul>
                    )}
                    <p className="text-caption text-muted">Max bid ${s?.max_bid}</p>
                  </div>
                )}
              </li>
            )
          })}
      </ul>
    </Section>
  )
}

function RecentSales({
  practice: p,
  names,
}: {
  practice: Practice
  names: Map<string, PlayerRow>
}) {
  const recent = p.room.sales.slice(-8).reverse()
  return (
    <Section title="Recent sales">
      {recent.length === 0 ? (
        <p className="text-subhead text-muted">Nothing sold yet.</p>
      ) : (
        <ul aria-label="Recent sales" className="flex flex-col divide-y divide-line">
          {recent.map((s) => (
            <SaleRow key={s.pid} pid={s.pid} names={names} price={s.price} note={s.team} />
          ))}
        </ul>
      )}
    </Section>
  )
}

function Done({
  practice: p,
  names,
  onAgain,
  onQuit,
}: {
  practice: Practice
  names: Map<string, PlayerRow>
  onAgain: (sameRoom: boolean) => void
  onQuit: () => void
}) {
  const [r] = useState(() =>
    buildReport(
      p.room.players,
      p.room.sales,
      p.room.teams,
      ME,
      p.settings.punted,
      p.room.budget,
      (pid) => names.get(pid)?.name ?? `Player ${pid}`,
    ),
  )
  const season = p.settings.season ?? null
  const strategy = `${season ? `${season} · ` : ''}${
    p.settings.punted === null
      ? 'All categories'
      : `Punt ${CATEGORIES[p.settings.punted]?.[1] ?? ''}`
  }`
  const [history] = useState(() =>
    addToHistory({
      id: `${p.settings.seed}:${p.settings.startedAt ?? ''}`,
      at: new Date().toISOString().slice(0, 10),
      seed: p.settings.seed,
      strategy,
      surplus: r.surplus,
      categoryWins: r.categoryWins,
    }),
  )
  const [saved] = useState(() => savedReport(p, r, names))
  // SIM-006: keep the run with the account (queued first, so an offline finish uploads later).
  const { sims, refresh } = useSimsApi()
  const runId = `${p.settings.seed}:${p.settings.startedAt ?? ''}`
  useEffect(() => {
    enqueue(runSim(runId, p.settings.season, strategy, r, saved, new Date().toISOString()))
    if (sims) void flush(sims).then(() => refresh())
    // once per finished run (the queue is idempotent by id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId])
  return (
    <div className="mx-auto flex w-full max-w-[880px] flex-col gap-5 px-5 pt-5 pb-8 min-[840px]:pt-8">
      <PageHeader
        eyebrow={season ? `${season} replay draft complete` : 'Practice draft complete'}
        title="Your report"
        trailing={<SampleBadge />}
      />
      <ReportView {...saved} />

      {season && <PlaySeason practice={p} season={season} />}

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => onAgain(false)}>Draft again</Button>
        <Button variant="secondary" onClick={() => onAgain(true)}>
          Replay this room
        </Button>
        <Button variant="secondary" onClick={onQuit}>
          Back to setup
        </Button>
      </div>

      {history.length > 1 && (
        <Section title="Your practice drafts">
          <table className="w-full text-subhead">
            <caption className="sr-only">Past practice drafts on this device</caption>
            <thead>
              <tr className="text-caption text-muted">
                <th scope="col" className="text-left font-medium">
                  Date
                </th>
                <th scope="col" className="text-left font-medium">
                  Strategy
                </th>
                <th scope="col" className="text-right font-medium">
                  Surplus
                </th>
                <th scope="col" className="text-right font-medium">
                  Category wins
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={`${h.seed}-${i}`} className="border-t border-line">
                  <td className="py-1.5 tabular-nums">{h.at}</td>
                  <td>{h.strategy}</td>
                  <td className="text-right tabular-nums">{signed(h.surplus)}</td>
                  <td className="text-right tabular-nums">{h.categoryWins}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}
      <p className="text-caption text-muted">
        The rivals are simulated managers, so this tells you about your plan, not about your
        league&apos;s real managers.
      </p>
    </div>
  )
}

/** SIM-002 AC2: keep this replay draft's league (16 rosters) and go play its season (SIM-004). */
function PlaySeason({ practice: p, season }: { practice: Practice; season: string }) {
  const navigate = useNavigate()
  const [existing] = useState(loadLeague)
  const [confirming, setConfirming] = useState(false)
  const { sims } = useSimsApi()
  const play = () => {
    const league = leagueFromSales(season, p.room.teams, ME, p.room.sales, new Date().toISOString())
    saveLeague(league)
    if (sims) void syncLeague(sims, league) // SIM-006: the season is kept with the account too
    void navigate('/replay')
  }
  return (
    <Card className="flex flex-col gap-3 p-4">
      <p className="text-headline">Play the {season} season</p>
      <p className="text-body text-ink-2">
        Take this team into {season}&apos;s real schedule: a weekly head-to-head against one of the
        15 rivals, daily lineups and up to 4 pickups a week, scored on what really happened.
      </p>
      {confirming ? (
        <div role="group" aria-label="Replace the saved season" className="flex flex-col gap-2">
          <p className="text-subhead">
            This replaces your saved {existing?.season} league
            {existing && Object.keys(existing.results).length > 0
              ? ` and its ${Object.keys(existing.results).length} played weeks`
              : ''}
            .
          </p>
          <div className="flex flex-wrap gap-2">
            <Button onClick={play}>Replace and play</Button>
            <Button variant="secondary" onClick={() => setConfirming(false)}>
              Keep the old one
            </Button>
          </div>
        </div>
      ) : (
        <Button onClick={() => (existing ? setConfirming(true) : play())}>
          Play the {season} season
        </Button>
      )}
    </Card>
  )
}

/** The report as a saved run keeps it: names and values of the players it mentions, not the whole pool. */
export function savedReport(p: Practice, r: Report, names: Map<string, PlayerRow>): SavedReport {
  const team = p.room.sales
    .filter((s) => s.team === ME)
    .map((s) => ({ pid: s.pid, price: s.price, value: Math.round(names.get(s.pid)?.dollars ?? 0) }))
  const mentioned = [
    ...team.map((t) => t.pid),
    ...r.bestBuys.map((b) => b.pid),
    ...r.overpays.map((b) => b.pid),
  ]
  return {
    report: r,
    names: Object.fromEntries(
      mentioned.map((pid) => [pid, names.get(pid)?.name ?? `Player ${pid}`]),
    ),
    team,
  }
}
