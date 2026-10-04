import { Link, useLocation } from 'react-router'
import { INTERACTIVE, cx } from './interactive'

export const tabs = [
  { to: '/today', label: 'Today', d: 'M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z' },
  { to: '/matchup', label: 'Matchup', d: 'M4 20V10M10 20V4M16 20v-7M22 20H2' },
  { to: '/waivers', label: 'Waivers', d: 'M12 5v14M5 12h14' },
  {
    to: '/players',
    label: 'Players',
    d: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  },
  { to: '/ask', label: 'Ask', d: 'M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z' },
]

/** WEB-029: the phone-only sixth tab; the desktop sidebar lists the same tools under Tools. */
const PRACTICE_PREFIXES = ['/practice', '/draft', '/replay', '/sims']
const practiceTab = {
  to: '/practice',
  label: 'Practice',
  d: 'M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 5V3M9.5 3h5M12 13l3-3',
}
const under = (pathname: string, prefix: string) =>
  pathname === prefix || pathname.startsWith(`${prefix}/`)
const isActive = (pathname: string, to: string) =>
  to === practiceTab.to ? PRACTICE_PREFIXES.some((p) => under(pathname, p)) : under(pathname, to)

/** The six tabs on the translucent material, items full-height (≥ 44 px), icon + label. */
export function TabBar() {
  const { pathname } = useLocation()
  return (
    <nav
      aria-label="Main"
      data-variant="tabs"
      className="material hairline-t grid grid-cols-6 px-1 pt-1.5 pb-[max(1.25rem,env(safe-area-inset-bottom))]"
    >
      {[...tabs, practiceTab].map((t) => {
        const active = isActive(pathname, t.to)
        return (
          <Link
            key={t.to}
            to={t.to}
            aria-current={active ? 'page' : undefined}
            className={cx(
              INTERACTIVE,
              'tab-item flex min-h-12 min-w-0 flex-col items-center justify-center gap-0.5 rounded-row text-caption transition-colors',
              active ? 'text-accent' : 'text-muted',
            )}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d={t.d} />
            </svg>
            {t.label}
          </Link>
        )
      })}
    </nav>
  )
}
