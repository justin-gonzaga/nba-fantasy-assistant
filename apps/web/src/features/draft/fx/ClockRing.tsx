import { useEffect, useRef } from 'react'
import { cx } from '../../../components/ui/interactive'
import { clockState } from './clock'

const SIZE = 56
const STROKE = 5
const R = (SIZE - STROKE) / 2
const C = 2 * Math.PI * R

const PHASE_STROKE = {
  calm: 'stroke-ink-2',
  warn: 'stroke-warn',
  urgent: 'stroke-urgent',
  expired: 'stroke-urgent',
} as const

/**
 * A ring that closes from full to empty. It follows the same `end` time as the digits, so it never
 * drifts; with reduced motion it steps once per second instead of animating.
 */
export function ClockRing({
  end,
  total,
  left,
  reduced,
}: {
  end: number
  total: number
  left: number
  reduced: boolean
}) {
  const arc = useRef<SVGCircleElement>(null)
  const { phase, fraction } = clockState(left, total)

  useEffect(() => {
    const el = arc.current
    if (!el) return
    if (reduced) {
      el.style.strokeDashoffset = String(C * (1 - fraction))
      return
    }
    let frame = 0
    const draw = () => {
      const f = Math.min(1, Math.max(0, (end - Date.now()) / (total * 1000)))
      el.style.strokeDashoffset = String(C * (1 - f))
      if (f > 0) frame = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(frame)
  }, [end, total, reduced, fraction])

  return (
    <div
      data-testid="clock-ring"
      data-phase={phase}
      className={cx('relative size-14 shrink-0', phase === 'urgent' && !reduced && 'ring-pulse')}
    >
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="size-full -rotate-90" aria-hidden="true">
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={R}
          fill="none"
          strokeWidth={STROKE}
          className="stroke-line"
        />
        <circle
          ref={arc}
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={R}
          fill="none"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - fraction)}
          className={PHASE_STROKE[phase]}
        />
      </svg>
      <span
        className={cx(
          'absolute inset-0 grid place-items-center text-headline tabular-nums',
          phase === 'urgent' || phase === 'expired' ? 'font-bold text-urgent' : 'font-medium',
        )}
      >
        {left}
        <span className="sr-only"> seconds</span>
      </span>
    </div>
  )
}
