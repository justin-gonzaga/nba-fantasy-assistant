import { useCallback, useEffect, useRef, type PointerEvent, type ReactNode } from 'react'
import { cx } from './interactive'

/** How far (px) a touch drag must pull the sheet down to close it. */
const CLOSE_AT = 80
/** The longest an exit may take before the sheet closes anyway (exit motion is 240 ms). */
const EXIT_FALLBACK_MS = 400

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * A modal sheet (design-language §3, §5). It rises from the bottom on phones and scales in on wider
 * screens; it focuses its first control and keeps Tab inside, locks the page scroll, and closes on
 * Escape, a backdrop click or a downward touch drag on the grabber — after its exit animation.
 * Render it while open; `onClose` runs once the sheet has animated out.
 */
export function Sheet({
  labelledBy,
  onClose,
  children,
}: {
  /** The id of the element that names the dialog (its title). */
  labelledBy: string
  onClose: () => void
  /** Content. A control marked `data-sheet-close` closes the sheet (animating out) when clicked. */
  children: ReactNode
}) {
  const backdropRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)
  const closing = useRef(false)
  const drag = useRef<{ id: number; startY: number; dy: number } | null>(null)

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  const requestClose = useCallback(() => {
    if (closing.current) return
    closing.current = true
    const parts = [backdropRef.current, panelRef.current].filter((el) => el !== null)
    for (const el of parts) el.dataset.state = 'closed'
    let done = false
    const finish = () => {
      if (done) return
      done = true
      onCloseRef.current()
    }
    // Wait for the exit animations; close at once where there are none (reduced support, tests).
    const running = parts.flatMap((el) => el.getAnimations?.() ?? [])
    if (running.length === 0) return finish()
    void Promise.allSettled(running.map((a) => a.finished)).then(finish)
    setTimeout(finish, EXIT_FALLBACK_MS)
  }, [])

  // Return focus to whatever opened the sheet once it unmounts (APG dialog pattern).
  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    return () => opener?.focus()
  }, [])

  // Focus the first control; Escape closes; Tab stays inside (WCAG 2.4.3).
  useEffect(() => {
    const panel = panelRef.current
    panel?.querySelector<HTMLElement>(FOCUSABLE)?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') return requestClose()
      if (e.key !== 'Tab' || !panel) return
      const focusable = panel.querySelectorAll<HTMLElement>(FOCUSABLE)
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last?.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first?.focus()
      }
    }
    // A control marked data-sheet-close (e.g. the Close button) closes with the exit animation.
    const onClick = (e: MouseEvent) => {
      if (e.target instanceof Element && e.target.closest('[data-sheet-close]')) requestClose()
    }
    document.addEventListener('keydown', onKey)
    panel?.addEventListener('click', onClick)
    return () => {
      document.removeEventListener('keydown', onKey)
      panel?.removeEventListener('click', onClick)
    }
  }, [requestClose])

  // The page behind doesn't scroll while the sheet is open.
  useEffect(() => {
    const before = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = before
    }
  }, [])

  const onDragStart = (e: PointerEvent<HTMLDivElement>) => {
    const panel = panelRef.current
    if (e.pointerType !== 'touch' || !panel) return
    drag.current = { id: e.pointerId, startY: e.clientY, dy: 0 }
    e.currentTarget.setPointerCapture?.(e.pointerId)
    panel.dataset.dragging = ''
  }
  const onDragMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current
    const panel = panelRef.current
    if (!d || !panel || e.pointerId !== d.id) return
    d.dy = Math.max(0, e.clientY - d.startY)
    panel.style.transform = `translateY(${d.dy}px)`
  }
  const onDragEnd = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current
    const panel = panelRef.current
    if (!d || !panel || e.pointerId !== d.id) return
    drag.current = null
    delete panel.dataset.dragging
    const dy = Math.max(d.dy, e.clientY - d.startY)
    if (e.type === 'pointerup' && dy > CLOSE_AT) requestClose()
    else panel.style.transform = '' // springs back on the sheet transition
  }

  return (
    <div className="fixed inset-0 z-20 flex items-end justify-center sm:items-center sm:p-5">
      <div
        ref={backdropRef}
        data-state="open"
        data-testid="sheet-backdrop"
        className="sheet-backdrop absolute inset-0"
        onClick={requestClose}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        data-state="open"
        className="sheet-panel material relative flex max-h-[90dvh] w-full max-w-md flex-col overflow-hidden rounded-t-sheet sm:rounded-sheet"
      >
        <div
          data-testid="sheet-grabber"
          aria-hidden="true"
          onPointerDown={onDragStart}
          onPointerMove={onDragMove}
          onPointerUp={onDragEnd}
          onPointerCancel={onDragEnd}
          className="flex shrink-0 cursor-grab touch-none justify-center pt-2 pb-1 sm:hidden"
        >
          <span className="h-1.5 w-10 rounded-full bg-line" />
        </div>
        <div
          className={cx(
            'flex flex-col gap-4 overflow-y-auto overscroll-contain px-5 pt-2 sm:pt-5',
            'pb-[max(1.25rem,env(safe-area-inset-bottom))]',
          )}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
