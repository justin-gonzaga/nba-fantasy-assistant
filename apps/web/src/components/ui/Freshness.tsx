import type { Freshness as F } from '../../api/types'

// A timestamp shows its Sydney time; a plain date (e.g. a projection's day) shows the date.
const when = (iso: string) =>
  iso.includes('T')
    ? new Date(iso).toLocaleTimeString('en-AU', {
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'Australia/Sydney',
      })
    : new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-AU', { day: 'numeric', month: 'short' })

export function Freshness({ f }: { f: F }) {
  const parts = [
    f.asOf ? `Updated ${when(f.asOf)}` : 'Not updated yet',
    ...f.sources.map((s) => `${s.name.toLowerCase()} ${s.asOf ? when(s.asOf) : 'missing'}`),
  ]
  return <p className="text-caption text-muted">{parts.join(' · ')}</p>
}
