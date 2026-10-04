import type { ButtonHTMLAttributes } from 'react'
import { INTERACTIVE, cx } from './interactive'
import { usePointerLight } from './usePointerLight'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  /** `row`: a card-like row that lifts and lights on hover. `bare`: inside a Surface that does that. */
  variant?: 'row' | 'bare'
}

/** A row or card button: pointer cursor, hover lift + light (fine pointers), press scale, focus ring. */
export function Pressable({
  variant = 'row',
  className,
  type = 'button',
  onPointerMove,
  ...rest
}: Props) {
  const light = usePointerLight(onPointerMove)
  return (
    <button
      type={type}
      onPointerMove={light}
      className={cx(
        INTERACTIVE,
        'press w-full text-left',
        variant === 'row' && 'surface lift light rounded-row',
        variant === 'bare' && 'rounded-[inherit]',
        className,
      )}
      {...rest}
    />
  )
}
