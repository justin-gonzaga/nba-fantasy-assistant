import { useSyncExternalStore } from 'react'

/** design-language §9 breakpoints (Material 3 window classes). */
export const EXPANDED = '(min-width: 840px)' // sidebar replaces the tab bar
export const LARGE = '(min-width: 1200px)' // list pages gain a right detail panel
export const WIDE = '(min-width: 1600px)' // the table keeps every column beside the panel

/** Whether a media query matches, kept in sync with the window (false where matchMedia is missing). */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      if (typeof window.matchMedia !== 'function') return () => {}
      const mq = window.matchMedia(query)
      mq.addEventListener('change', onChange)
      return () => mq.removeEventListener('change', onChange)
    },
    () => typeof window.matchMedia === 'function' && window.matchMedia(query).matches,
    () => false,
  )
}
