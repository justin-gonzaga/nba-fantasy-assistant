import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router'
import { INTERACTIVE, cx } from './interactive'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }

/** An action button: 44 px tall, presses to 0.96; primary brightens and secondary gains surface-2 on hover. */
const look = (variant: 'primary' | 'secondary', className?: string) =>
  cx(
    INTERACTIVE,
    'press-strong inline-flex min-h-11 items-center justify-center rounded-row px-4 text-subhead font-semibold',
    variant === 'primary' ? 'btn-primary' : 'btn-secondary',
    className,
  )

export function Button({ variant = 'primary', className, type = 'button', ...rest }: Props) {
  return <button type={type} className={look(variant, className)} {...rest} />
}

/** A navigation that looks and behaves like a Button (same target size, hover, press, focus). */
export function ButtonLink({
  variant = 'secondary',
  className,
  ...rest
}: LinkProps & { variant?: 'primary' | 'secondary' }) {
  return <Link className={look(variant, className)} {...rest} />
}
