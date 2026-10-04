// WEB-024: the desktop toolbar's Filters popover and the removable active-filter chips.
import { useEffect, useId, useRef, useState } from 'react'
import { Chip } from '../../components/ui/Chip'
import { INTERACTIVE, cx } from '../../components/ui/interactive'

export type FilterChip = { code: string; text: string; count: number; on: boolean }

function Group({
  label,
  chips,
  toggle,
}: {
  label: string
  chips: FilterChip[]
  toggle: (code: string) => void
}) {
  if (chips.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <p className="text-caption tracking-eyebrow text-muted uppercase" aria-hidden="true">
        {label.replace('Filter by ', '')}
      </p>
      <div role="group" aria-label={label} className="flex flex-wrap gap-2">
        {chips.map((c) => (
          <Chip key={c.code} pressed={c.on} onClick={() => toggle(c.code)}>
            {c.text} <span className="text-muted tabular-nums">{c.count}</span>
          </Chip>
        ))}
      </div>
    </div>
  )
}

/** A disclosure: Escape or a click outside closes it and focus goes back to the button. */
export function FiltersPopover({
  badges,
  signals,
  toggleBadge,
  toggleSignal,
}: {
  badges: FilterChip[]
  signals: FilterChip[]
  toggleBadge: (code: string) => void
  toggleSignal: (code: string) => void
}) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const box = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const active = [...badges, ...signals].filter((c) => c.on).length

  useEffect(() => {
    if (!open) return
    // Capture phase + stopPropagation: Escape closes only the popover, never an open panel too.
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      e.stopPropagation()
      setOpen(false)
      button.current?.focus()
    }
    const onDown = (e: MouseEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener('keydown', onKey, true)
    document.addEventListener('mousedown', onDown)
    return () => {
      window.removeEventListener('keydown', onKey, true)
      document.removeEventListener('mousedown', onDown)
    }
  }, [open])

  if (badges.length === 0 && signals.length === 0) return null
  return (
    <div ref={box} className="relative">
      <button
        ref={button}
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        className={cx(
          INTERACTIVE,
          'surface press inline-flex min-h-10 items-center gap-2 rounded-chip px-3 text-subhead',
          open && 'border-accent',
        )}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M3 6h18M7 12h10M10 18h4" />
        </svg>
        Filters
        {active > 0 && (
          <span
            aria-hidden="true"
            className="grid min-w-5 place-items-center rounded-full bg-button px-1 text-caption text-button-ink tabular-nums"
          >
            {active}
          </span>
        )}
      </button>
      {open && (
        <div
          id={id}
          className="surface absolute top-full right-0 z-20 mt-2 flex w-80 flex-col gap-4 rounded-card p-4"
        >
          <Group label="Filter by badge" chips={badges} toggle={toggleBadge} />
          <Group label="Filter by signal" chips={signals} toggle={toggleSignal} />
        </div>
      )}
    </div>
  )
}

/** The chosen filters under the toolbar; each one removes itself. */
export function ActiveFilters({
  chips,
  remove,
  clear,
}: {
  chips: { key: string; text: string }[]
  remove: (key: string) => void
  clear: () => void
}) {
  if (chips.length === 0) return null
  return (
    <div className="flex flex-wrap items-center gap-2">
      {chips.map((c) => (
        <button
          key={c.key}
          type="button"
          aria-label={`Remove filter: ${c.text}`}
          onClick={() => remove(c.key)}
          className={cx(
            INTERACTIVE,
            'press inline-flex min-h-8 items-center gap-1.5 rounded-full bg-accent-tint px-3 text-caption font-medium text-accent-ink',
          )}
        >
          {c.text}
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.25"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      ))}
      {chips.length > 1 && (
        <button
          type="button"
          onClick={clear}
          className={cx(INTERACTIVE, 'rounded-chip text-caption text-ink-2 underline')}
        >
          Clear all
        </button>
      )}
    </div>
  )
}
