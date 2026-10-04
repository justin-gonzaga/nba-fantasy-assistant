import type { Freshness } from '../../api/types'
import { Button, ButtonLink } from './Button'
import { StateCard } from './StateCard'

const day = (iso: string) =>
  new Date(`${iso}T12:00:00Z`)
    .toLocaleDateString('en-AU', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      timeZone: 'UTC',
    })
    .replace(',', '') // "Tue 20 Oct" (design language §6)

/** WEB-016: shown at the top of a brief page when the NBA data didn't update (INFRA-007). */
export function StaleNotice({ f }: { f: Freshness }) {
  if (!f.staleSince) return null
  return (
    <StateCard tone="warn" title={`Data from ${day(f.staleSince)}`}>
      Today’s NBA update didn’t run, so this uses the last data we have.
    </StateCard>
  )
}

/** A page that crashed while rendering: the tab bar keeps working (route error element). */
export function RouteCrash() {
  return (
    <div className="px-5 pt-5">
      <StateCard
        tone="error"
        title="This page hit a problem"
        action={
          <Button variant="secondary" onClick={() => window.location.reload()}>
            Reload
          </Button>
        }
      >
        The other tabs still work.
      </StateCard>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="px-5 pt-5">
      <StateCard title="Page not found" action={<ButtonLink to="/today">Go to Today</ButtonLink>}>
        That address doesn’t exist in this app.
      </StateCard>
    </div>
  )
}
