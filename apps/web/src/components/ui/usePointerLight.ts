import { useCallback, type PointerEvent } from 'react'

/**
 * Moves the hover light (`.light`, design-language §4) with a mouse: writes the pointer position into the
 * element's `--x` / `--y` CSS variables. Touch and pen pointers are ignored, so a tap never leaves a lit
 * surface behind. It writes the style directly (no React state), so moving the pointer never re-renders.
 */
export function usePointerLight<T extends HTMLElement>(
  onPointerMove?: (e: PointerEvent<T>) => void,
): (e: PointerEvent<T>) => void {
  return useCallback(
    (e: PointerEvent<T>) => {
      onPointerMove?.(e)
      if (e.pointerType !== 'mouse') return
      const el = e.currentTarget
      const box = el.getBoundingClientRect()
      el.style.setProperty('--x', `${e.clientX - box.left}px`)
      el.style.setProperty('--y', `${e.clientY - box.top}px`)
    },
    [onPointerMove],
  )
}
