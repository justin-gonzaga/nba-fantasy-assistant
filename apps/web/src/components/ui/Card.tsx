import type { ReactNode } from 'react'
import { Surface } from './Surface'

/** A static card (a Surface): 16 px padding unless `className` sets its own. */
export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <Surface className={className}>{children}</Surface>
}
