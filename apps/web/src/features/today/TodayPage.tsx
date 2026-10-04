import { useState } from 'react'
import { useToday } from '../../api/client'
import type { Action } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Freshness } from '../../components/ui/Freshness'
import { PageHeader } from '../../components/ui/PageHeader'
import { Pressable } from '../../components/ui/Pressable'
import { StaleNotice } from '../../components/ui/PageStates'
import { QueryState } from '../../components/ui/QueryState'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { Surface } from '../../components/ui/Surface'
import { LARGE, useMediaQuery } from '../../components/ui/useMediaQuery'
import { WinLabel } from '../../components/ui/WinLabel'

const KIND = { lineup: 'LINEUP', injury: 'INJURY', stream: 'STREAM' } as const

// WEB-000 pick: Today B, the scoreboard first, then a compact "Do today" list whose rows open
// the action card with its why.
export function TodayPage() {
  const q = useToday()
  const large = useMediaQuery(LARGE)
  return (
    <QueryState
      q={q}
      notReady={{
        title: 'Your daily brief starts with the season',
        body: 'Once games begin, Today shows your projected category scoreboard and what to do each day. Meanwhile, the Players tab has draft values.',
      }}
    >
      {(t) => {
        const scoreboard = t.matchup && (
          <Card className="px-4 py-2">
            <table className="w-full text-body">
              <caption className="sr-only">Projected category results this week</caption>
              <thead>
                <tr className="text-left text-caption text-muted">
                  <th scope="col" className="py-1 font-medium">
                    Cat
                  </th>
                  <th scope="col" className="font-medium">
                    You
                  </th>
                  <th scope="col" className="font-medium">
                    {t.matchup.opponent ?? 'Them'}
                  </th>
                  <th scope="col" className="text-right font-medium">
                    Projected
                  </th>
                </tr>
              </thead>
              <tbody>
                {t.matchup.categories.map((c) => (
                  <tr key={c.code} className="border-t border-line">
                    <th scope="row" className="py-2 text-left font-semibold">
                      {c.code}
                    </th>
                    <td className="text-subhead tabular-nums">{c.mine}</td>
                    <td className="text-subhead text-muted tabular-nums">{c.theirs}</td>
                    <td className="text-right">
                      <WinLabel p={c.winProb} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )
        const todo = (
          <section className="flex flex-col gap-2" aria-labelledby="todo">
            <h2
              id="todo"
              className="text-caption font-semibold tracking-eyebrow text-muted uppercase"
            >
              Do today
            </h2>
            {t.actions.length === 0 ? (
              <p className="py-2 text-body text-muted">Nothing to do today: your lineup is set.</p>
            ) : (
              <div className="stagger flex flex-col gap-2">
                {t.actions.map((a) => (
                  <ActionRow key={a.id} a={a} />
                ))}
              </div>
            )}
          </section>
        )
        const header = (
          <>
            <PageHeader
              eyebrow={
                new Date(t.date).toLocaleDateString('en-AU', {
                  weekday: 'short',
                  day: 'numeric',
                  month: 'short',
                }) + (t.matchup?.opponent ? ` · vs ${t.matchup.opponent}` : '')
              }
              title={
                t.matchup?.record
                  ? `${t.matchup.record.wins}–${t.matchup.record.losses}–${t.matchup.record.ties}`
                  : t.matchup
                    ? `${t.matchup.expectedCategories.toFixed(1)} of 9 expected`
                    : 'No matchup this week'
              }
              trailing={<SampleBadge />}
            />
            <StaleNotice f={t.freshness} />
          </>
        )
        // WEB-026 (§9): ≥ 1200 px the actions read first on the left, the scoreboard stays in view.
        if (large && scoreboard)
          return (
            <div className="flex flex-col gap-4 pt-8 pb-4">
              {header}
              <div
                data-testid="today-columns"
                className="grid grid-cols-[minmax(0,1fr)_400px] items-start gap-6"
              >
                <div className="flex flex-col gap-4">
                  {todo}
                  <Freshness f={t.freshness} />
                </div>
                <div className="sticky top-6">{scoreboard}</div>
              </div>
            </div>
          )
        return (
          <div className="mx-auto flex w-full max-w-[760px] flex-col gap-4 px-5 pt-5 pb-4">
            {header}
            {scoreboard}
            {todo}
            <Freshness f={t.freshness} />
          </div>
        )
      }}
    </QueryState>
  )
}

function ActionRow({ a }: { a: Action }) {
  const [open, setOpen] = useState(false)
  return (
    <Surface interactive className="p-0">
      <Pressable
        variant="bare"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex min-h-11 items-center gap-3 px-3.5 py-3"
      >
        <span className="w-14 shrink-0 text-caption font-bold tracking-eyebrow text-accent-ink">
          {KIND[a.kind]}
        </span>
        <span className="flex-1 text-body">{a.title}</span>
        <span aria-hidden="true" className="text-headline text-muted">
          {open ? '−' : '›'}
        </span>
      </Pressable>
      {open && (
        <div className="reveal flex flex-col gap-3 border-t border-line px-3.5 py-3">
          <p className="text-body text-ink-2">{a.detail}</p>
          <div className="rounded-row bg-ground p-3 text-subhead text-ink-2">
            <p className="font-semibold text-ink">Why</p>
            <ul className="list-disc pl-4">
              {a.why.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
            {(a.confidence || a.deadline) && (
              <p className="text-muted">
                {[a.confidence && `Confidence: ${a.confidence}`, a.deadline]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            )}
          </div>
          {a.cta && <Button>{a.cta}</Button>}
        </div>
      )}
    </Surface>
  )
}
