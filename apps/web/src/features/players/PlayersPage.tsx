import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { usePlayers } from '../../api/client'
import { ApiError } from '../../api/http'
import type { PlayerRow } from '../../api/types'
import { Avatar } from '../../components/ui/Avatar'
import { Button } from '../../components/ui/Button'
import { Chip } from '../../components/ui/Chip'
import { Freshness } from '../../components/ui/Freshness'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { PageHeader } from '../../components/ui/PageHeader'
import { ProblemCard } from '../../components/ui/QueryState'
import { Pressable } from '../../components/ui/Pressable'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { Skeleton } from '../../components/ui/Skeleton'
import { EXPANDED, LARGE, WIDE, useMediaQuery } from '../../components/ui/useMediaQuery'
import { FILTERS, hasAnyBadge, parseBadgeParam } from './badges'
import { ActiveFilters, FiltersPopover } from './FiltersPopover'
import { PlayerDetail } from './PlayerDetail'
import { RowBadges } from './PlayerBadges'
import { PlayersTable, type SortDir } from './PlayersTable'
import {
  INDICATOR_SORTS,
  SIGNAL_FILTERS,
  hasAnySignal,
  hasIndicators,
  indicatorKey,
  parseSignalParam,
} from './indicators'
import {
  CATEGORIES,
  CATEGORY_KEYS,
  MIN_MPG,
  fold,
  hasPosition,
  headshotUrl,
  inRotation,
  strategyLabel,
} from './format'

const PAGE = 50
const POSITIONS = ['All', 'G', 'F', 'C'] as const
const SORTS: [string, string][] = [
  ['rank', 'Rank'],
  ['dollars', '$ value'],
  ...CATEGORIES.map(([k, label]): [string, string] => [k, `Best ${label}`]),
]

const HEALTHY_SORT: [string, string] = ['healthy', 'Healthy rank']

/** Ranks read best-first ascending; every other key is "more is better", so descending. */
const naturalDir = (sort: string): SortDir =>
  sort === 'rank' || sort === 'healthy' ? 'asc' : 'desc'

function sortKey(p: PlayerRow, sort: string): number {
  if (sort === 'rank') return p.rank
  if (sort === 'healthy') return p.healthyRank ?? Infinity
  if (sort === 'certainty' || sort === 'role') return indicatorKey(p, sort)
  if (sort === 'dollars') return p.dollars
  return p.strengths[sort] ?? -Infinity
}

function sorted(players: PlayerRow[], sort: string, dir: SortDir): PlayerRow[] {
  const sign = dir === 'asc' ? 1 : -1
  // NaN (∞ − ∞) is falsy, so missing values fall through to the rank tie-break.
  const byKey = (a: PlayerRow, b: PlayerRow) =>
    (sortKey(a, sort) - sortKey(b, sort)) * sign || a.rank - b.rank
  if (!CATEGORY_KEYS.has(sort)) return [...players].sort(byKey)
  // WEB-027: in a category sort only draftable rotation players are ranked (TO otherwise rewards
  // sitting); everyone else follows in rank order.
  const ranked = (p: PlayerRow) => p.inPool && inRotation(p)
  const rotation = players.filter(ranked).sort(byKey)
  const rest = players.filter((p) => !ranked(p)).sort((a, b) => a.rank - b.rank)
  return [...rotation, ...rest]
}

const field = 'surface rounded-chip text-ink focus-visible:outline-2 focus-visible:outline-accent'
const select = cx(field, INTERACTIVE, 'min-h-11 w-full px-2.5 text-subhead')
const label = 'flex flex-col gap-1 text-caption tracking-eyebrow text-muted uppercase'

// WEB-005: every projected player with the draft values, under all categories or a punt strategy.
// Search, position, badges, sort and strategy live in the URL, so back, refresh and links keep them.
// WEB-024: ≥ 840 px a toolbar + sortable table; ≥ 1200 px the detail sits in a right panel.
export function PlayersPage() {
  const [params, setParams] = useSearchParams()
  const desktop = useMediaQuery(EXPANDED)
  const large = useMediaQuery(LARGE)
  const wide = useMediaQuery(WIDE)
  const q = params.get('q') ?? ''
  const pos = params.get('pos') ?? 'All'
  const sort = params.get('sort') ?? 'rank'
  const dir: SortDir =
    params.get('dir') === 'asc' || params.get('dir') === 'desc'
      ? (params.get('dir') as SortDir)
      : naturalDir(sort)
  const variant = params.get('variant') ?? 'all'
  const badgeParam = params.get('badge')
  const chosen = useMemo(() => parseBadgeParam(badgeParam), [badgeParam])
  const sigParam = params.get('sig')
  const signals = useMemo(() => parseSignalParam(sigParam), [sigParam])
  const query = usePlayers(variant)
  // Paging restarts whenever the filters change.
  const filterKey = [q, pos, chosen.join(','), signals.join(','), sort, dir, variant].join('|')
  const [page, setPage] = useState({ key: filterKey, n: PAGE })
  if (page.key !== filterKey) setPage({ key: filterKey, n: PAGE }) // adjust during render
  const limit = page.key === filterKey ? page.n : PAGE
  const [open, setOpen] = useState<PlayerRow | null>(null)
  const trigger = useRef<HTMLButtonElement | null>(null)

  const update = (changes: Record<string, string | null>) =>
    setParams(
      (p) => {
        const next = new URLSearchParams(p)
        for (const [k, v] of Object.entries(changes)) {
          if (v === null) next.delete(k)
          else next.set(k, v)
        }
        return next
      },
      { replace: true },
    )
  const set = (key: string, value: string, fallback: string) =>
    update({ [key]: value === fallback ? null : value })

  // A header click sorts by that column; a second click flips the direction.
  const sortBy = (key: string) => {
    if (key !== sort) return update({ sort: key === 'rank' ? null : key, dir: null })
    const flipped: SortDir = dir === 'asc' ? 'desc' : 'asc'
    update({ dir: flipped === naturalDir(sort) ? null : flipped })
  }

  // A stale or hand-typed strategy in the URL falls back to all categories.
  const invalidVariant =
    query.error instanceof ApiError && query.error.status === 422 && variant !== 'all'
  useEffect(() => {
    if (!invalidVariant) return
    setParams(
      (p) => {
        const next = new URLSearchParams(p)
        next.delete('variant')
        return next
      },
      { replace: true },
    )
  }, [invalidVariant, setParams])

  const players = query.data?.players
  const shown = useMemo(() => {
    if (!players) return []
    const needle = fold(q.trim())
    const filtered = players.filter(
      (p) =>
        (needle === '' || fold(p.name).includes(needle)) &&
        (pos === 'All' || hasPosition(p.positions, pos)) &&
        hasAnyBadge(p, chosen) &&
        hasAnySignal(p, signals),
    )
    return sorted(filtered, sort, dir)
  }, [players, q, pos, chosen, signals, sort, dir])

  const close = useCallback(() => {
    setOpen(null)
    trigger.current?.focus()
  }, [])
  const openPlayer = (p: PlayerRow, el: HTMLButtonElement) => {
    trigger.current = el
    setOpen(p)
  }

  if (query.isPending || invalidVariant)
    return (
      <div role="status" className="flex flex-col gap-2 px-5 pt-5" aria-label="Loading players">
        <p className="text-subhead text-muted">Loading players…</p>
        {[0, 1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    )

  if (query.isError)
    return (
      <div className="px-5 pt-5">
        <ProblemCard
          error={query.error}
          retry={() => void query.refetch()}
          notReady={{
            title: 'Player values aren’t published yet',
            body: 'They appear after the pre-season projection run publishes auction values.',
          }}
        />
      </div>
    )

  const data = query.data
  const total = data.players.length
  const filtering = q !== '' || pos !== 'All' || chosen.length > 0 || signals.length > 0
  const withIndicators = hasIndicators(data.players)
  // WEB-022: counts on every chip; a chip that would match nobody is hidden unless selected.
  const badgeChips = FILTERS.map(
    ([code, text]) =>
      [code, text, data.players.filter((p) => hasAnyBadge(p, [code])).length] as const,
  ).filter(([code, , n]) => n > 0 || chosen.includes(code))
  const signalChips = withIndicators
    ? SIGNAL_FILTERS.map(
        ([code, text]) =>
          [code, text, data.players.filter((p) => hasAnySignal(p, [code])).length] as const,
      ).filter(([code, , n]) => n > 0 || signals.includes(code))
    : []
  const toggleSignal = (code: string) =>
    set(
      'sig',
      SIGNAL_FILTERS.map(([c]) => c)
        .filter((c) => (c === code ? !signals.includes(c) : signals.includes(c)))
        .join(','),
      '',
    )
  const toggleBadge = (code: string) =>
    set(
      'badge',
      FILTERS.map(([c]) => c)
        .filter((c) => (c === code ? !chosen.includes(c) : chosen.includes(c)))
        .join(','),
      '',
    )
  const clearFilters = () => setParams(variant === 'all' ? {} : { variant }, { replace: true })

  const strategySelect = (
    <select
      aria-label="Strategy"
      value={variant}
      onChange={(e) => set('variant', e.target.value, 'all')}
      className={select}
    >
      {data.variants.map((v) => (
        <option key={v} value={v}>
          {strategyLabel(v)}
        </option>
      ))}
    </select>
  )
  const sortSelect = (
    <select
      aria-label="Sort"
      value={sort}
      onChange={(e) =>
        update({ sort: e.target.value === 'rank' ? null : e.target.value, dir: null })
      }
      className={select}
    >
      {[
        ...SORTS,
        ...(players?.some((p) => p.healthyRank != null) ? [HEALTHY_SORT] : []),
        ...(withIndicators ? INDICATOR_SORTS : []),
      ].map(([k, text]) => (
        <option key={k} value={k}>
          {text}
        </option>
      ))}
    </select>
  )
  const positionGroup = (
    <div role="group" aria-label="Filter by position" className="flex gap-2">
      {POSITIONS.map((x) => (
        <Chip key={x} pressed={pos === x} onClick={() => set('pos', x, 'All')}>
          {x}
        </Chip>
      ))}
    </div>
  )
  const search = (
    <input
      type="search"
      aria-label="Search players"
      placeholder="Search players"
      value={q}
      onChange={(e) => set('q', e.target.value, '')}
      className={cx(field, 'min-h-11 w-full px-3 text-body placeholder:text-muted')}
    />
  )
  const count = (
    <p className="text-caption text-muted" aria-live="polite">
      {filtering ? `${shown.length} of ${total} players` : `${total} players`}
      {query.isPlaceholderData && ' · updating…'}
    </p>
  )
  const empty = (
    <div className="flex flex-col items-start gap-2 py-6">
      <p className="text-body font-semibold">No players match</p>
      <button
        type="button"
        onClick={clearFilters}
        className={cx(INTERACTIVE, 'min-h-11 rounded-chip text-body text-accent underline')}
      >
        Clear filters
      </button>
    </div>
  )
  const more = shown.length > limit && (
    <Button variant="secondary" onClick={() => setPage({ key: filterKey, n: limit + PAGE })}>
      Show more
    </Button>
  )
  const notes = (data.badgeNotes ?? []).length > 0 && (
    <p className="text-caption text-muted">{(data.badgeNotes ?? []).join(' · ')}</p>
  )
  const detail = open && (
    <PlayerDetail
      player={open}
      players={data.players}
      variant={variant}
      notes={data.badgeNotes ?? []}
      onClose={close}
      layout={large ? 'panel' : 'sheet'}
    />
  )

  if (desktop) {
    const label = (list: readonly (readonly [string, string])[], code: string) =>
      list.find(([c]) => c === code)?.[1] ?? code
    return (
      <div className="flex flex-col gap-4 pt-8 pb-4">
        <PageHeader title="Players" trailing={<SampleBadge />} />
        <p className="-mt-2 text-subhead text-ink-2">
          Auction values and season projections, ranked for your scoring.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <div className="min-w-56 flex-1">{search}</div>
          <div className="w-44">{strategySelect}</div>
          {positionGroup}
          <div className="w-40">{sortSelect}</div>
          <FiltersPopover
            badges={badgeChips.map(([code, text, n]) => ({
              code,
              text,
              count: n,
              on: chosen.includes(code),
            }))}
            signals={signalChips.map(([code, text, n]) => ({
              code,
              text,
              count: n,
              on: signals.includes(code),
            }))}
            toggleBadge={toggleBadge}
            toggleSignal={toggleSignal}
          />
        </div>
        <ActiveFilters
          chips={[
            ...chosen.map((c) => ({ key: `badge:${c}`, text: label(FILTERS, c) })),
            ...signals.map((c) => ({ key: `sig:${c}`, text: label(SIGNAL_FILTERS, c) })),
          ]}
          remove={(key) => {
            const [kind, code] = key.split(':') as [string, string]
            if (kind === 'badge') toggleBadge(code)
            else toggleSignal(code)
          }}
          clear={() => update({ badge: null, sig: null })}
        />
        {notes}
        <div className="flex items-baseline justify-between gap-4">
          {count}
          <p className="text-caption text-muted">
            Category columns sort by fantasy impact for {strategyLabel(variant).toLowerCase()};
            players outside the draft pool or under {MIN_MPG}
            min/game sort last.
          </p>
        </div>
        <div
          className={cx(large && open && 'grid grid-cols-[minmax(0,1fr)_380px] items-start gap-6')}
        >
          <div className="flex min-w-0 flex-col gap-3">
            {shown.length === 0 ? (
              empty
            ) : (
              <PlayersTable
                players={shown.slice(0, limit)}
                sort={sort}
                dir={dir}
                onSort={sortBy}
                onOpen={openPlayer}
                selectedId={open?.id ?? null}
                busy={query.isPlaceholderData}
                compact={large && !!open && !wide}
              />
            )}
            {more}
          </div>
          {large && detail}
        </div>
        <Freshness f={data.freshness} />
        {!large && detail}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 px-5 pt-5 pb-4">
      <PageHeader title="Players" trailing={<SampleBadge />} />
      <p className="text-subhead text-ink-2">
        Auction values and season projections, ranked for your scoring.{' '}
        <Link to="/draft" className={cx(INTERACTIVE, 'rounded-chip text-accent-ink underline')}>
          Practise the draft
        </Link>
      </p>
      {search}
      <div className="grid grid-cols-2 gap-2">
        <label className={label}>
          Strategy
          {strategySelect}
        </label>
        <label className={label}>
          Sort
          {sortSelect}
        </label>
      </div>
      {positionGroup}
      {badgeChips.length > 0 && (
        <div role="group" aria-label="Filter by badge" className="flex flex-wrap gap-2">
          {badgeChips.map(([code, text, n]) => (
            <Chip key={code} pressed={chosen.includes(code)} onClick={() => toggleBadge(code)}>
              {text} <span className="tabular-nums text-muted">{n}</span>
            </Chip>
          ))}
        </div>
      )}
      {signalChips.length > 0 && (
        <div role="group" aria-label="Filter by signal" className="flex flex-wrap gap-2">
          {signalChips.map(([code, text, n]) => (
            <Chip key={code} pressed={signals.includes(code)} onClick={() => toggleSignal(code)}>
              {text} <span className="tabular-nums text-muted">{n}</span>
            </Chip>
          ))}
        </div>
      )}
      {notes}
      {count}
      {shown.length === 0 ? (
        empty
      ) : (
        <ol
          aria-label="Players"
          aria-busy={query.isPlaceholderData}
          className="stagger flex flex-col gap-2"
        >
          {shown.slice(0, limit).map((p) => (
            <li key={p.id}>
              <Pressable
                onClick={(e) => openPlayer(p, e.currentTarget)}
                className="grid grid-cols-[28px_40px_1fr_auto] items-center gap-2.5 px-3 py-2.5"
              >
                <span className="tabular-nums text-subhead text-muted">{p.rank}</span>
                <Avatar src={headshotUrl(p.id)} name={p.name} size={40} />
                <span className="flex min-w-0 flex-col gap-0.5">
                  <span className="truncate text-body font-semibold">{p.name}</span>
                  {(p.team || p.positions) && (
                    <span className="text-subhead text-muted">
                      {[p.team, p.positions].filter(Boolean).join(' · ')}
                    </span>
                  )}
                  <RowBadges player={p} />
                </span>
                <span className="flex flex-col items-end">
                  <span className={cx('tabular-nums text-body', !p.inPool && 'text-muted')}>
                    ${Math.round(p.dollars)}
                  </span>
                  <span className="text-caption text-muted">Tier {p.tier}</span>
                </span>
              </Pressable>
            </li>
          ))}
        </ol>
      )}
      {more}
      <Freshness f={data.freshness} />
      {detail}
    </div>
  )
}
