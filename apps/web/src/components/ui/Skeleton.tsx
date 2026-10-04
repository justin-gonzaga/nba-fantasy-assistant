import { cx } from './interactive'

/** A placeholder block with a slow shimmer (none under reduced motion). Size it with `className`. */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cx('skeleton rounded-row', className)} />
}
