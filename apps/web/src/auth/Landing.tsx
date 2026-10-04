// WEB-026: the signed-out landing (design-language §9). Every claim here is true of the system today;
// no user counts, ratings or testimonials (AC4).
import { useId, useState } from 'react'
import { samplePlayers } from '../api/fixtures'
import type { PlayerRow } from '../api/types'
import { Button } from '../components/ui/Button'
import { PlayerBadgeChip } from '../features/players/PlayerBadges'
import { badgesOf } from '../features/players/badges'

const STEPS: [string, string][] = [
  [
    'Fresh data every morning',
    'NBA box scores, injury reports and your Yahoo league are collected overnight and kept with their history.',
  ],
  [
    'Projections with certainty',
    'Players carry range and certainty indicators, so a safe pick and a gamble don’t look the same.',
  ],
  [
    'Advice with reasons',
    'Draft values, lineup calls and waiver moves each show the evidence behind them.',
  ],
]

const PRINCIPLES: [string, string][] = [
  [
    'Checked before it ships',
    'A model replaces the simple baseline only after it beats it on past seasons.',
  ],
  ['No made-up explanations', 'Every reason shown comes from the data, never from a guess.'],
  [
    'Your league stays private',
    'Other managers are pseudonymised, and live league data is never public.',
  ],
]

const initials = (name: string) =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)

/** A still of the real Players table, built from the same components, on sample players. */
function Preview() {
  const rows = samplePlayers.players.slice(0, 5) as PlayerRow[]
  return (
    <div
      role="img"
      aria-label="Preview of the Players table with sample data"
      className="surface overflow-hidden rounded-card"
    >
      <div className="flex items-center gap-1.5 border-b border-line px-4 py-3" aria-hidden="true">
        <span className="size-2.5 rounded-full bg-line" />
        <span className="size-2.5 rounded-full bg-line" />
        <span className="size-2.5 rounded-full bg-line" />
        <span className="ml-3 text-caption text-muted">Players · All categories</span>
      </div>
      <table className="w-full" aria-hidden="true">
        <thead>
          <tr className="text-caption text-muted">
            <th className="py-2 pl-4 text-right font-medium">#</th>
            <th className="px-3 py-2 text-left font-medium">Player</th>
            <th className="px-2 py-2 text-right font-medium">$</th>
            <th className="px-2 py-2 text-right font-medium">PTS</th>
            <th className="px-2 py-2 text-right font-medium hidden min-[480px]:table-cell">REB</th>
            <th className="py-2 pr-4 pl-2 text-right font-medium hidden min-[480px]:table-cell">
              AST
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => {
            const badge = badgesOf(p)[0]
            return (
              <tr key={p.id} className="border-t border-line text-subhead even:bg-ground/60">
                <td className="py-2.5 pl-4 text-right text-muted tabular-nums">{p.rank}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-tint text-caption font-semibold text-accent-ink">
                      {initials(p.name)}
                    </span>
                    <div className="flex min-w-0 flex-col gap-0.5">
                      <span className="truncate font-semibold">{p.name}</span>
                      <span className="flex flex-wrap items-center gap-1.5 text-caption text-muted">
                        {[p.team, p.positions].filter(Boolean).join(' · ')}
                        {badge && <PlayerBadgeChip badge={badge} />}
                      </span>
                    </div>
                  </div>
                </td>
                <td className="px-2 py-2.5 text-right font-semibold tabular-nums">
                  ${Math.round(p.dollars)}
                </td>
                <td className="py-2.5 pr-4 pl-2 text-right text-ink-2 tabular-nums min-[480px]:pr-2">
                  {p.projection?.pts.toFixed(1)}
                </td>
                <td className="px-2 py-2.5 text-right text-ink-2 tabular-nums hidden min-[480px]:table-cell">
                  {p.projection?.reb.toFixed(1)}
                </td>
                <td className="py-2.5 pr-4 pl-2 text-right text-ink-2 tabular-nums hidden min-[480px]:table-cell">
                  {p.projection?.ast.toFixed(1)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function Section({
  title,
  items,
  numbered = false,
}: {
  title: string
  items: [string, string][]
  numbered?: boolean
}) {
  const id = useId()
  const List = numbered ? 'ol' : 'ul'
  return (
    <section aria-labelledby={id} className="flex flex-col gap-5">
      <h2 id={id} className="text-title-lg">
        {title}
      </h2>
      <List className="grid gap-4 min-[840px]:grid-cols-3">
        {items.map(([head, body], i) => (
          <li key={head} className="surface flex flex-col gap-2 rounded-card p-5">
            {numbered && (
              <span
                aria-hidden="true"
                className="grid size-7 place-items-center rounded-full bg-accent-tint text-caption font-semibold text-accent-ink"
              >
                {i + 1}
              </span>
            )}
            <h3 className="text-headline">{head}</h3>
            <p className="text-subhead text-ink-2">{body}</p>
          </li>
        ))}
      </List>
    </section>
  )
}

/** The signed-out home: what this is, how it works, and the two ways in. */
export function Landing({
  signIn,
  onExplore,
}: {
  signIn: () => Promise<void>
  onExplore?: () => void
}) {
  const [error, setError] = useState<string | null>(null)
  return (
    <main className="min-h-dvh bg-ground">
      <div className="mx-auto flex max-w-[1120px] flex-col gap-16 px-5 py-8 min-[840px]:gap-24 min-[840px]:px-8 min-[840px]:py-12">
        <div className="flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-row bg-button text-caption font-bold text-button-ink"
          >
            FA
          </span>
          <span className="text-headline font-semibold tracking-tight">Fantasy Assistant</span>
        </div>

        <div className="reveal grid items-center gap-10 min-[1100px]:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
          <div className="flex max-w-[34rem] flex-col gap-5">
            <p className="text-caption font-semibold tracking-eyebrow text-accent-ink uppercase">
              NBA fantasy · Yahoo head-to-head
            </p>
            <h1 className="text-display text-balance">
              Draft and manage your fantasy team with numbers you can check.
            </h1>
            <p className="text-body text-ink-2">
              Auction values, category projections and a daily to-do for your Yahoo league, each
              with the reasons behind it.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                onClick={() => {
                  setError(null)
                  signIn().catch((e: unknown) => {
                    setError(e instanceof Error ? e.message : 'Sign-in failed')
                  })
                }}
              >
                Sign in with Google
              </Button>
              {onExplore && (
                <Button variant="secondary" onClick={onExplore}>
                  Explore with sample data
                </Button>
              )}
            </div>
            {error && (
              <p role="alert" className="text-subhead text-lose">
                {error}
              </p>
            )}
            <p className="text-caption text-muted">
              Access is by invitation. The sample shows how it works without an account.
            </p>
          </div>
          <Preview />
        </div>

        <Section title="How it works" items={STEPS} numbered />
        <Section title="Principles" items={PRINCIPLES} />

        <footer className="border-t border-line pt-6 text-caption text-muted">
          A personal project. Not affiliated with the NBA or Yahoo.
        </footer>
      </div>
    </main>
  )
}
