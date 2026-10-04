import type { ButtonHTMLAttributes } from 'react'
import { INTERACTIVE, cx } from './interactive'

type Props = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-pressed'> & { pressed: boolean }

/** A toggle chip (filters): reports aria-pressed, presses to 0.96. */
export function Chip({ pressed, className, type = 'button', ...rest }: Props) {
  return (
    <button
      type={type}
      aria-pressed={pressed}
      className={cx(
        INTERACTIVE,
        'chip press-strong min-h-11 rounded-full px-3.5 text-subhead font-medium',
        className,
      )}
      {...rest}
    />
  )
}
