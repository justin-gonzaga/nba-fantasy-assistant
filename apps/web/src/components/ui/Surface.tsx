import type { HTMLAttributes } from 'react'
import { cx } from './interactive'
import { usePointerLight } from './usePointerLight'

type Props = HTMLAttributes<HTMLElement> & {
  as?: 'div' | 'li' | 'section' | 'article'
  /** Lifts to elevation 2 and follows a mouse with the light (its child is the control). */
  interactive?: boolean
  /** 16 px for cards, 12 px for list rows. */
  radius?: 'card' | 'row'
}

/** A card: hairline, elevation 1, 16 px radius. Padding is the caller's (default 16 px). */
export function Surface({
  as: Tag = 'div',
  interactive = false,
  radius = 'card',
  className,
  onPointerMove,
  ...rest
}: Props) {
  const light = usePointerLight(onPointerMove)
  return (
    <Tag
      onPointerMove={interactive ? light : onPointerMove}
      className={cx(
        'surface',
        radius === 'card' ? 'rounded-card' : 'rounded-row',
        interactive && 'lift light',
        className ?? 'p-4',
      )}
      {...rest}
    />
  )
}
