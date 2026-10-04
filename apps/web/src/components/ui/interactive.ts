// Classes every interactive primitive shares (design-language §4): the pointer cursor, not-allowed when
// disabled, and the focus-visible ring (2px accent, 2px offset).
export const INTERACTIVE =
  'cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent'

export const cx = (...parts: (string | false | null | undefined)[]) =>
  parts.filter(Boolean).join(' ')
