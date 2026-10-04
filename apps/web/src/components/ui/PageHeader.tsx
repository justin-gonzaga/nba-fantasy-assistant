import type { ReactNode } from 'react'

/** A page's large title, with an optional eyebrow line above it and a trailing slot (badges). */
export function PageHeader({
  title,
  eyebrow,
  trailing,
}: {
  title: ReactNode
  eyebrow?: ReactNode
  trailing?: ReactNode
}) {
  return (
    <header className="flex items-end justify-between gap-3">
      <div className="flex min-w-0 flex-col gap-0.5">
        {eyebrow && <p className="text-subhead text-muted">{eyebrow}</p>}
        <h1 className="text-title-lg">{title}</h1>
      </div>
      {trailing && <div className="shrink-0 pb-1">{trailing}</div>}
    </header>
  )
}
