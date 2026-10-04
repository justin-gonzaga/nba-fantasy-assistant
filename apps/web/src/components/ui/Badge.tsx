import type { ReactNode } from 'react'
import { cx } from './interactive'

export type Tone = 'neutral' | 'accent' | 'win' | 'lose' | 'warn'

// Opaque fills (the tone mixed into the surface), so a badge reads the same on any row: zebra,
// hover or selected (WEB-024: translucent fills dropped below 4.5:1 on tinted rows).
const TONE: Record<Tone, string> = {
  neutral: 'bg-surface-2 text-ink-2',
  accent: 'bg-accent-tint text-accent-ink',
  win: 'badge-win text-win',
  lose: 'badge-lose text-lose',
  warn: 'badge-warn text-warn',
}

/** A small label. Colour is never the only signal: it always has words, and optionally an icon. */
export function Badge({
  tone = 'neutral',
  icon,
  children,
  className,
}: {
  tone?: Tone
  icon?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-caption font-semibold whitespace-nowrap',
        TONE[tone],
        className,
      )}
    >
      {icon && <span aria-hidden="true">{icon}</span>}
      {children}
    </span>
  )
}
