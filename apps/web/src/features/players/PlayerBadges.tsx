// WEB-018: badge visuals — design-language Badge with a stroke icon and a word.
import type { PlayerRow } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { IndicatorChip } from './DecisionPanel'
import { ROW_BADGES, badgesOf, type BadgeCode, type PlayerBadge } from './badges'

// 24-grid stroke icons (Lucide-compatible paths): circle-alert, bandage, calendar-x, sparkles,
// arrow-up-right, sprout, star.
const ICONS: Record<BadgeCode, string[]> = {
  injured_today: ['M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z', 'M12 8v4', 'M12 16h.01'],
  // pencil: an owner-reviewed adjustment with a cited source (DATA-036)
  adjusted: [
    'M21.17 6.81a1 1 0 0 0-3.99-3.99L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z',
    'm15 5 4 4',
  ],
  injury_prone: [
    'M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z',
    'M6 6v12',
    'M18 6v12',
    'M10 10h.01',
    'M14 10h.01',
    'M10 14h.01',
    'M14 14h.01',
  ],
  missed_time: [
    'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z',
    'M8 2v4',
    'M16 2v4',
    'M3 10h18',
    'm14 14-4 4',
    'm10 14 4 4',
  ],
  breakout: [
    'M9.94 15.5a2 2 0 0 0-1.44-1.44l-6.13-1.58a.5.5 0 0 1 0-.96L8.5 9.94a2 2 0 0 0 1.44-1.44l1.58-6.13a.5.5 0 0 1 .96 0l1.58 6.13a2 2 0 0 0 1.44 1.44l6.13 1.58a.5.5 0 0 1 0 .96l-6.13 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.13a.5.5 0 0 1-.96 0z',
  ],
  bounce_back: ['M7 7h10v10', 'M7 17 17 7'],
  rookie: [
    'M7 20h10',
    'M10 20c5.5-2.5.8-6.4 3-10',
    'M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z',
    'M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z',
  ],
  top_tier: [
    'M11.53 2.3a.53.53 0 0 1 .95 0l2.31 4.68a2.12 2.12 0 0 0 1.6 1.16l5.16.75a.53.53 0 0 1 .3.91l-3.74 3.64a2.12 2.12 0 0 0-.61 1.88l.88 5.14a.53.53 0 0 1-.77.56l-4.62-2.43a2.12 2.12 0 0 0-1.97 0L6.4 21.01a.53.53 0 0 1-.77-.56l.88-5.14a2.12 2.12 0 0 0-.61-1.88L2.16 9.8a.53.53 0 0 1 .3-.91l5.16-.75a2.12 2.12 0 0 0 1.6-1.16z',
  ],
}

function BadgeIcon({ code }: { code: BadgeCode }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="-my-0.5"
    >
      {ICONS[code].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}

/** One badge: the icon is decorative, the word is what a screen reader hears. */
export function PlayerBadgeChip({ badge }: { badge: PlayerBadge }) {
  return (
    <Badge tone={badge.tone} icon={<BadgeIcon code={badge.code} />}>
      {badge.label}
    </Badge>
  )
}

/**
 * The row's chips under one priority (WEB-018 badges first, then the WEB-020 signal): at most
 * ROW_BADGES, then "+N"; everything lives in the detail sheet.
 */
export function RowBadges({ player }: { player: PlayerRow }) {
  const chips = [
    ...badgesOf(player).map((b) => <PlayerBadgeChip key={b.code} badge={b} />),
    ...(player.signal
      ? [
          <span key="signal" data-testid="signal-chip">
            <IndicatorChip indicator={player.signal} />
          </span>,
        ]
      : []),
  ]
  if (chips.length === 0) return null
  const extra = chips.length - ROW_BADGES
  return (
    <span className="flex flex-wrap items-center gap-1" data-testid="row-badges">
      {chips.slice(0, ROW_BADGES)}
      {extra > 0 && (
        <span className="text-caption font-semibold text-muted">
          +{extra}
          <span className="sr-only"> more {extra === 1 ? 'label' : 'labels'}</span>
        </span>
      )}
    </span>
  )
}
