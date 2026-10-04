import { useState } from 'react'
import { useWaivers } from '../../api/client'
import { Chip } from '../../components/ui/Chip'
import { Freshness } from '../../components/ui/Freshness'
import { PageHeader } from '../../components/ui/PageHeader'
import { StaleNotice } from '../../components/ui/PageStates'
import { QueryState } from '../../components/ui/QueryState'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { Surface } from '../../components/ui/Surface'

const FILTERS = ['All', 'BLK', 'REB', 'STL'] as const
type Filter = (typeof FILTERS)[number]

// WEB-000 pick: Waivers A, ranked by category wins gained this week, with filter chips.
export function WaiversPage() {
  const q = useWaivers()
  const [f, setF] = useState<Filter>('All')
  return (
    <QueryState
      q={q}
      notReady={{
        title: 'Waiver picks start with the season',
        body: 'Once games begin, Waivers ranks free agents by the category wins they add for your team this week.',
      }}
    >
      {(w) => {
        const shown = f === 'All' ? w.candidates : w.candidates.filter((c) => c.helps.includes(f))
        return (
          <div className="flex flex-col gap-3 px-5 pt-5 pb-4">
            <PageHeader title="Waivers" trailing={<SampleBadge />} />
            <StaleNotice f={w.freshness} />
            <p className="text-subhead text-ink-2">
              Ranked for your team by category wins gained ({w.horizon}).
            </p>
            <div role="group" aria-label="Filter by category" className="flex gap-2">
              {FILTERS.map((x) => (
                <Chip key={x} pressed={f === x} onClick={() => setF(x)}>
                  {x}
                </Chip>
              ))}
            </div>
            {shown.length === 0 ? (
              <p className="py-6 text-body text-muted">
                {w.candidates.length === 0
                  ? 'No free agent helps your team this week.'
                  : `No free agent helps ${f} this week.`}
              </p>
            ) : (
              <ol className="stagger flex flex-col gap-2">
                {shown.map((c, i) => (
                  <Surface
                    as="li"
                    radius="row"
                    key={c.id}
                    className="grid grid-cols-[24px_1fr_auto] items-center gap-2.5 px-3.5 py-3"
                  >
                    <span className="tabular-nums text-subhead text-muted">{i + 1}</span>
                    <span className="flex flex-col gap-1">
                      <span className="text-body font-semibold">{c.name}</span>
                      <span className="text-subhead text-muted">
                        {[c.team, c.positions, `${c.gamesLeft} games left`]
                          .filter(Boolean)
                          .join(' · ')}
                      </span>
                      <span className="text-subhead font-medium text-win">
                        Helps {c.helps.join(', ')}
                      </span>
                    </span>
                    <span className="flex flex-col items-end">
                      <span className="tabular-nums text-body">+{c.gain.toFixed(2)}</span>
                      <span className="text-caption text-muted">cat. wins</span>
                    </span>
                  </Surface>
                ))}
              </ol>
            )}
            {w.suggestedDrop && (
              <p className="text-subhead text-muted">Suggested drop: {w.suggestedDrop}.</p>
            )}
            <Freshness f={w.freshness} />
          </div>
        )
      }}
    </QueryState>
  )
}
