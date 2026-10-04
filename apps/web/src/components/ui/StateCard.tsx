import type { ReactNode } from 'react'
import { cx } from './interactive'
import { Surface } from './Surface'

export type StateTone = 'neutral' | 'warn' | 'error'

// One icon per tone so colour is never the only signal (design language §2, §4).
const ICON: Record<StateTone, string> = {
  neutral: 'M12 8v4l2.5 1.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z', // clock: not yet
  warn: 'M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  error: 'M12 8v4M12 16h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
}
const INK: Record<StateTone, string> = {
  neutral: 'text-muted',
  warn: 'text-warn',
  error: 'text-lose',
}

/**
 * WEB-016: the one layout for every non-data state (not ready, empty, error, offline, coming soon).
 * Neutral states are a polite `status`; only failures are an `alert`.
 */
export function StateCard({
  tone = 'neutral',
  title,
  children,
  action,
}: {
  tone?: StateTone
  title: string
  children?: ReactNode
  action?: ReactNode
}) {
  return (
    <Surface className="flex flex-col items-start gap-2 p-5">
      <div role={tone === 'error' ? 'alert' : 'status'} className="flex flex-col gap-2">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          className={cx(INK[tone])}
        >
          <path d={ICON[tone]} />
        </svg>
        <p className="text-headline">{title}</p>
        {children && <div className="text-subhead text-ink-2">{children}</div>}
      </div>
      {action && <div className="pt-1">{action}</div>}
    </Surface>
  )
}
