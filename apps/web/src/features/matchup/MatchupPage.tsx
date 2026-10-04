import { useState } from 'react'
import { useMatchup } from '../../api/client'
import { Card } from '../../components/ui/Card'
import { Freshness } from '../../components/ui/Freshness'
import { PageHeader } from '../../components/ui/PageHeader'
import { Pressable } from '../../components/ui/Pressable'
import { StaleNotice } from '../../components/ui/PageStates'
import { QueryState } from '../../components/ui/QueryState'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { WinLabel, winState } from '../../components/ui/WinLabel'

const BAR: Record<string, string> = {
  'text-win': 'bg-win',
  'text-lose': 'bg-lose',
  'text-even': 'bg-even',
}

// WEB-000 pick: Matchup A, all nine categories with a win-chance bar; tap one for what moves it.
export function MatchupPage() {
  const q = useMatchup()
  const [open, setOpen] = useState<string | null>(null)
  return (
    <QueryState
      q={q}
      notReady={{
        title: 'Your matchup appears once the season starts',
        body: 'Each week shows the nine categories against your opponent, with your chance in each. Meanwhile, the Players tab has draft values.',
      }}
    >
      {(m) => (
        <div className="flex flex-col gap-3 px-5 pt-5 pb-4">
          <PageHeader
            title="Matchup"
            eyebrow={`Week of ${new Date(`${m.weekStart}T12:00:00Z`).toLocaleDateString('en-AU', {
              day: 'numeric',
              month: 'short',
            })} · ${m.daysLeft} days left`}
            trailing={<SampleBadge />}
          />
          <StaleNotice f={m.freshness} />
          <Card className="grid grid-cols-[1fr_auto_1fr] items-center p-4">
            <span>
              <span className="block text-caption text-muted">You</span>
              <span className="text-body font-semibold">Your team</span>
            </span>
            <p className="tabular-nums text-title-lg">
              {m.record ? `${m.record.wins}–${m.record.losses}–${m.record.ties}` : 'vs'}
            </p>
            <span className="text-right">
              <span className="block text-caption text-muted">Opponent</span>
              <span className="text-body font-semibold">{m.opponent ?? 'Opponent'}</span>
            </span>
          </Card>
          <p className="text-subhead text-ink-2">
            Expected categories won this week:{' '}
            <strong className="tabular-nums text-win">
              {m.expectedCategories.toFixed(1)} of 9
            </strong>
            . Tap a category for what moves it.
          </p>
          <ul className="stagger flex flex-col gap-2">
            {m.categories.map((c) => {
              const isOpen = open === c.code
              return (
                <li key={c.code}>
                  <Pressable
                    aria-expanded={isOpen}
                    onClick={() => setOpen(isOpen ? null : c.code)}
                    className="flex flex-col gap-2 px-3.5 py-3"
                  >
                    <span className="grid w-full grid-cols-[48px_1fr_112px] items-center gap-2">
                      <span className="text-body font-semibold">{c.code}</span>
                      <span className="flex flex-col gap-1">
                        <span className="tabular-nums text-caption text-ink-2">
                          {c.mine} vs {c.theirs}
                        </span>
                        <span className="flex h-1.5 rounded-full bg-line">
                          <span
                            className={`h-1.5 rounded-full ${BAR[winState(c.winProb).tone] ?? 'bg-even'}`}
                            style={{ width: `${Math.round(c.winProb * 100)}%` }}
                          />
                        </span>
                      </span>
                      <span className="text-right">
                        <WinLabel p={c.winProb} showPct />
                      </span>
                    </span>
                    {isOpen && (
                      <span className="reveal text-subhead text-ink-2">
                        {c.note ?? 'No note for this category yet.'}
                      </span>
                    )}
                  </Pressable>
                </li>
              )
            })}
          </ul>
          <Freshness f={m.freshness} />
        </div>
      )}
    </QueryState>
  )
}
