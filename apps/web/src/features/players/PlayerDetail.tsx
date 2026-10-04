import { useId } from 'react'
import type { PlayerRow } from '../../api/types'
import { Avatar } from '../../components/ui/Avatar'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { Panel } from '../../components/ui/Panel'
import { Sheet } from '../../components/ui/Sheet'
import { DecisionPanel } from './DecisionPanel'
import { PlayerBadgeChip } from './PlayerBadges'
import { badgesOf } from './badges'
import { CATEGORIES, headshotUrl, pct, signed, strategyLabel } from './format'
import { categoryPercentiles, type CategoryPercentile } from './percentiles'

type Projection = NonNullable<PlayerRow['projection']>

/** The projected line, box-score order (§9: one row, no orphan cells). */
const LINE: [string, (p: Projection) => string][] = [
  ['G', (p) => String(Math.round(p.games))],
  ['MIN', (p) => p.mpg.toFixed(1)],
  ['PTS', (p) => p.pts.toFixed(1)],
  ['REB', (p) => p.reb.toFixed(1)],
  ['AST', (p) => p.ast.toFixed(1)],
  ['STL', (p) => p.stl.toFixed(1)],
  ['BLK', (p) => p.blk.toFixed(1)],
  ['3PM', (p) => p.fg3m.toFixed(1)],
  ['TOV', (p) => p.tov.toFixed(1)],
  ['FG%', (p) => pct(p.fgPct)],
  ['FT%', (p) => pct(p.ftPct)],
]

const ordinal = (n: number) => {
  const tens = n % 100
  if (tens >= 11 && tens <= 13) return `${n}th`
  return `${n}${['th', 'st', 'nd', 'rd'][n % 10] ?? 'th'}`
}

function SectionTitle({ id, children }: { id: string; children: string }) {
  return (
    <h3 id={id} className="text-subhead font-semibold">
      {children}
    </h3>
  )
}

/** design-language §9: one bar per category, 0–100 against the expected draft pool. */
function PercentileBars({ items, poolSize }: { items: CategoryPercentile[]; poolSize: number }) {
  return (
    <>
      <p className="text-caption text-muted">
        Percentile against the {poolSize} players in the expected draft pool.
      </p>
      <ul className="flex flex-col gap-2">
        {items.map((c) => (
          <li key={c.key} className="grid grid-cols-[40px_1fr_32px] items-center gap-3">
            <span className="text-caption font-medium">{c.label}</span>
            <span
              role="meter"
              aria-label={`${c.label}: ${ordinal(c.percentile)} percentile`}
              aria-valuenow={c.percentile}
              aria-valuemin={0}
              aria-valuemax={100}
              className="relative h-1.5 overflow-hidden rounded-full bg-line"
            >
              <span
                className={cx(
                  'absolute inset-y-0 left-0 rounded-full',
                  c.percentile >= 67 ? 'bg-win' : c.percentile <= 33 ? 'bg-lose' : 'bg-even',
                )}
                style={{ width: `${Math.max(c.percentile, 2)}%` }}
              />
            </span>
            <span className="text-right text-caption text-ink-2 tabular-nums">{c.percentile}</span>
          </li>
        ))}
      </ul>
      <p className="text-caption text-muted">TOV: higher = fewer turnovers</p>
    </>
  )
}

/** Fallback under 20 pool players: the standardized strengths, centred on zero. */
function StrengthBars({ player: p }: { player: PlayerRow }) {
  const max = Math.max(1, ...Object.values(p.strengths).map(Math.abs))
  return (
    <>
      <p className="text-caption text-muted">
        Standardized against the draft pool: + helps your team, − hurts it.
      </p>
      <ul className="flex flex-col gap-2">
        {CATEGORIES.map(([k, label]) => {
          const v = p.strengths[k] ?? 0
          const w = `${(Math.abs(v) / max) * 50}%`
          return (
            <li key={k} className="grid grid-cols-[40px_1fr_48px] items-center gap-3">
              <span className="text-caption font-medium">{label}</span>
              <span className="relative h-1.5 rounded-full bg-line" aria-hidden="true">
                <span
                  className={cx('absolute inset-y-0 rounded-full', v < 0 ? 'bg-lose' : 'bg-win')}
                  style={v < 0 ? { right: '50%', width: w } : { left: '50%', width: w }}
                />
              </span>
              <span className="text-right text-caption text-ink-2 tabular-nums">{signed(v)}</span>
            </li>
          )
        })}
      </ul>
    </>
  )
}

/** One player in §9 order: identity → key figures → category profile → line → indicators → badges. */
export function PlayerDetail({
  player: p,
  players = [],
  variant,
  notes = [],
  onClose,
  layout = 'sheet',
}: {
  player: PlayerRow
  /** Everyone on the page, for the percentile pool. */
  players?: readonly PlayerRow[]
  variant: string
  notes?: string[] // badge inputs not published yet (WEB-018)
  onClose: () => void
  /** WEB-024: beside the list at >= 1200 px; otherwise a modal sheet. */
  layout?: 'sheet' | 'panel'
}) {
  const titleId = useId()
  const Frame = layout === 'panel' ? Panel : Sheet
  const profileId = useId()
  const lineId = useId()
  const badgesId = useId()
  const badges = badgesOf(p)
  const proj = p.projection
  const percentiles = categoryPercentiles(p, players)
  const poolSize = players.filter((x) => x.inPool).length
  const figures: [string, string][] = [
    ['Value', `$${Math.round(p.dollars)}`],
    ['Rank', `#${p.rank}`],
    ...(p.healthyRank != null ? [['Healthy rank', `#${p.healthyRank}`] as [string, string]] : []),
    ['Tier', String(p.tier)],
  ]
  return (
    <Frame labelledBy={titleId} onClose={onClose}>
      <div className="flex items-start gap-4">
        <Avatar src={headshotUrl(p.id)} name={p.name} size={64} />
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <h2 id={titleId} className="text-title">
            {p.name}
          </h2>
          <p className="text-subhead text-muted">
            {[p.team, p.positions].filter(Boolean).join(' · ') || 'Team and position unknown'}
          </p>
          {badges.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1" data-testid="detail-badges">
              {badges.map((b) => (
                <PlayerBadgeChip key={b.code} badge={b} />
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          data-sheet-close
          aria-label="Close"
          className={cx(
            INTERACTIVE,
            'btn-secondary press-strong flex size-11 shrink-0 items-center justify-center rounded-full',
          )}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex flex-col gap-1.5">
        <ul
          aria-label="Key figures"
          className="surface grid auto-cols-fr grid-flow-col divide-x divide-line rounded-row"
        >
          {figures.map(([k, v]) => (
            <li key={k} className="flex flex-col items-center gap-0.5 px-2 py-2.5">
              <span className="text-caption tracking-eyebrow text-muted uppercase">{k}</span>
              <span className="text-headline font-semibold tabular-nums">{v}</span>
            </li>
          ))}
        </ul>
        <p className="text-caption text-muted">
          {strategyLabel(variant)}
          {!p.inPool && ' · outside the expected draft pool'}
        </p>
        {p.healthyRank != null && proj && (
          <p className="text-subhead text-ink-2">
            Ranked #{p.rank} after expected missed games ({Math.round(proj.games)} of 82); #
            {p.healthyRank} if he plays 72.
          </p>
        )}
      </div>

      <section className="flex flex-col gap-2" aria-labelledby={profileId}>
        <SectionTitle id={profileId}>Category profile</SectionTitle>
        {percentiles ? (
          <PercentileBars items={percentiles} poolSize={poolSize} />
        ) : (
          <StrengthBars player={p} />
        )}
      </section>

      <section className="flex flex-col gap-2" aria-labelledby={lineId}>
        <SectionTitle id={lineId}>Projected per game</SectionTitle>
        {proj ? (
          <>
            <div className="-mx-1 overflow-x-auto px-1">
              <table aria-labelledby={lineId} className="w-full text-center">
                <thead>
                  <tr className="text-caption text-muted">
                    {LINE.map(([label]) => (
                      <th key={label} scope="col" className="pb-1 font-medium">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="hairline-t text-subhead tabular-nums">
                    {LINE.map(([label, fmt]) => (
                      <td key={label} className="pt-1.5">
                        {fmt(proj)}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-caption text-muted">
              G is games over the season; the rest per game.
            </p>
          </>
        ) : (
          <p className="text-body text-muted">No projection yet</p>
        )}
      </section>

      <DecisionPanel player={p} />

      <section className="flex flex-col gap-2" aria-labelledby={badgesId}>
        <SectionTitle id={badgesId}>Badges</SectionTitle>
        {badges.length > 0 ? (
          <ul aria-labelledby={badgesId} className="flex flex-col gap-2">
            {badges.map((b) => (
              <li key={b.code} className="grid grid-cols-[auto_1fr] items-baseline gap-x-3">
                <span className="text-subhead font-medium">{b.label}</span>
                <span className="text-subhead text-ink-2">{b.why}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-body text-muted">No badges</p>
        )}
        {notes.map((n) => (
          <p key={n} className="text-caption text-muted">
            {n}
          </p>
        ))}
      </section>
    </Frame>
  )
}
