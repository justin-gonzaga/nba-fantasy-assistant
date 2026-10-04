// WEB-020: the row's one signal chip and the detail's "At a glance" panel.
import { useId } from 'react'
import type { PlayerRow } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import type { PlayerIndicator } from './indicators'

// 24-grid stroke icons (Lucide-compatible): trending-up/down, gauge, activity, ruler, puzzle, user.
const ICONS: Record<PlayerIndicator['code'], string[]> = {
  role: ['M22 7 13.5 15.5 8.5 10.5 2 17', 'M16 7h6v6'],
  certainty: ['m12 14 4-4', 'M3.34 19a10 10 0 1 1 17.32 0'],
  consistency: ['M22 12h-4l-3 9L9 3l-3 9H2'],
  range: ['M3 12h18', 'M7 8v8', 'M17 8v8'],
  punt_fit: [
    'M19.44 7.85c-.49.49-.29 1.37.33 1.69a2.5 2.5 0 1 1-3.31 3.31c-.32-.62-1.2-.82-1.69-.33l-1.3 1.3a1 1 0 0 0 0 1.41l1.3 1.3c.49.49.29 1.37-.33 1.69a2.5 2.5 0 1 0 3.31 3.31',
  ],
  age: ['M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
}

function IndicatorIcon({ code }: { code: PlayerIndicator['code'] }) {
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

export function IndicatorChip({ indicator }: { indicator: PlayerIndicator }) {
  return (
    <Badge tone={indicator.tone} icon={<IndicatorIcon code={indicator.code} />}>
      {indicator.label}
    </Badge>
  )
}

/** Every indicator with its why line; absent when none are published. */
export function DecisionPanel({ player }: { player: PlayerRow }) {
  const id = useId()
  const items = player.indicators ?? []
  if (items.length === 0) return null
  return (
    <section className="flex flex-col gap-2" aria-labelledby={id}>
      <h3 id={id} className="text-subhead font-semibold">
        At a glance
      </h3>
      {/* §9: a definition list — the indicator, then its one-line reason beside it (stacked on phones). */}
      <dl className="grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-[minmax(0,11rem)_1fr] sm:gap-y-2.5">
        {items.map((i) => (
          <div key={i.code} className="contents">
            <dt className="pt-1 sm:pt-0">
              <IndicatorChip indicator={i} />
            </dt>
            <dd className="text-subhead text-ink-2">{i.why}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
