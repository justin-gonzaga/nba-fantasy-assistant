// WEB-029: one place on the phone tab bar for every practice tool. It only links: pages keep their own state.
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Card } from '../../components/ui/Card'
import { INTERACTIVE, cx } from '../../components/ui/interactive'
import { PageHeader } from '../../components/ui/PageHeader'
import { loadSave } from '../draft/practice'
import { loadLeague } from '../replay/league'

const row = cx(
  INTERACTIVE,
  'press flex min-h-14 flex-col justify-center gap-0.5 rounded-row px-4 py-3',
)

function Entry({ to, title, children }: { to: string; title: string; children: ReactNode }) {
  return (
    <Link to={to} className={row}>
      <span className="text-headline font-semibold">{title}</span>
      <span className="text-subhead text-muted">{children}</span>
    </Link>
  )
}

export function PracticeHub() {
  const draft = loadSave()
  const league = loadLeague()
  return (
    <div className="mx-auto flex w-full max-w-[640px] flex-col gap-4 px-5 pt-5 pb-8 min-[840px]:pt-8">
      <PageHeader title="Practice" eyebrow="Get ready for the draft" />
      {(draft || league) && (
        <Card className="flex flex-col p-1.5">
          {draft && (
            <Entry to="/draft" title="Resume your draft">
              Pick up where you left off in the practice room.
            </Entry>
          )}
          {league && (
            <Entry to="/replay" title="Resume your season">
              Your {league.season} league, week by week.
            </Entry>
          )}
        </Card>
      )}
      <Card className="flex flex-col p-1.5">
        <Entry to="/draft" title="Draft practice">
          A mock auction against 15 other teams, with live advice.
        </Entry>
        <Entry to="/replay" title="Season replay">
          Draft a past season, then play its weeks against your rivals.
        </Entry>
        <Entry to="/sims" title="Past sims">
          Your saved drafts and seasons. Sign in to keep them.
        </Entry>
      </Card>
    </div>
  )
}
