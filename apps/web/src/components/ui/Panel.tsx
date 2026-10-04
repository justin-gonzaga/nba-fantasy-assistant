import { useEffect, useRef, type ReactNode } from 'react'

/**
 * design-language §9: the ≥ 1200 px detail panel beside a list. Not modal: the list stays usable.
 * Its first control takes focus when opened; it closes on Escape or a `data-sheet-close` control (the Sheet's
 * contract, so the same content renders in either), and leaves focus handling on close to the opener.
 */
export function Panel({
  labelledBy,
  onClose,
  children,
}: {
  labelledBy: string
  onClose: () => void
  children: ReactNode
}) {
  const ref = useRef<HTMLElement>(null)
  const onCloseRef = useRef(onClose)
  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    const panel = ref.current
    // Like the sheet: focus lands on the first control (Close), so keyboard users start inside.
    const first = panel?.querySelector<HTMLElement>('button, [href], input, select, textarea')
    ;(first ?? panel)?.focus({ preventScroll: true })
    // Bubble phase on document: a popover inside the page claims Escape first (capture + stopPropagation).
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current()
    }
    const onClick = (e: MouseEvent) => {
      if (e.target instanceof Element && e.target.closest('[data-sheet-close]'))
        onCloseRef.current()
    }
    document.addEventListener('keydown', onKey)
    panel?.addEventListener('click', onClick)
    return () => {
      document.removeEventListener('keydown', onKey)
      panel?.removeEventListener('click', onClick)
    }
  }, [])

  return (
    <aside
      ref={ref}
      tabIndex={-1}
      aria-labelledby={labelledBy}
      className="surface reveal sticky top-6 flex max-h-[calc(100dvh-3rem)] flex-col gap-5 overflow-y-auto rounded-card p-5 outline-none"
    >
      {children}
    </aside>
  )
}
