import { NavLink } from 'react-router'
import { useSampleMode, useSession } from '../../auth/auth'
import { INTERACTIVE, cx } from './interactive'
import { tabs } from './TabBar'

/** design-language §9: the ≥ 840 px navigation — brand, the five destinations, the account at the foot. */
export function Sidebar() {
  const session = useSession()
  const sampleMode = useSampleMode()
  return (
    <aside className="hairline-r bg-surface">
      <div className="sticky top-0 flex h-dvh flex-col px-3 pt-6 pb-5">
        <div className="flex items-center gap-2.5 px-3 pb-6">
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-row bg-button text-caption font-bold text-button-ink"
          >
            FA
          </span>
          <span className="text-headline font-semibold tracking-tight">Fantasy Assistant</span>
        </div>
        <nav aria-label="Main" data-variant="sidebar" className="flex flex-col gap-0.5">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                cx(
                  INTERACTIVE,
                  'press flex min-h-10 items-center gap-3 rounded-row px-3 text-body transition-colors',
                  isActive
                    ? 'bg-accent-tint font-semibold text-accent-ink'
                    : 'text-ink-2 hover:bg-surface-2 hover:text-ink',
                )
              }
            >
              <svg
                width="20"
                height="20"
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
            </NavLink>
          ))}
        </nav>
        <nav aria-label="Tools" className="mt-6 flex flex-col gap-0.5">
          <p className="px-3 pb-1 text-caption tracking-eyebrow text-muted uppercase">Tools</p>
          <NavLink
            to="/draft"
            className={({ isActive }) =>
              cx(
                INTERACTIVE,
                'press flex min-h-10 items-center gap-3 rounded-row px-3 text-body transition-colors',
                isActive
                  ? 'bg-accent-tint font-semibold text-accent-ink'
                  : 'text-ink-2 hover:bg-surface-2 hover:text-ink',
              )
            }
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="m14.5 12.5-8 8a2.12 2.12 0 1 1-3-3l8-8M16 16l6-6M8 8l6-6M9 7l8 8M21 11l-8-8" />
            </svg>
            Draft practice
          </NavLink>
          <NavLink
            to="/replay"
            className={({ isActive }) =>
              cx(
                INTERACTIVE,
                'press flex min-h-10 items-center gap-3 rounded-row px-3 text-body transition-colors',
                isActive
                  ? 'bg-accent-tint font-semibold text-accent-ink'
                  : 'text-ink-2 hover:bg-surface-2 hover:text-ink',
              )
            }
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M3 4h18v17H3zM3 9h18M8 2v4M16 2v4M7 13h2M11 13h2M15 13h2M7 17h2M11 17h2" />
            </svg>
            Season replay
          </NavLink>
          <NavLink
            to="/sims"
            className={({ isActive }) =>
              cx(
                INTERACTIVE,
                'press flex min-h-10 items-center gap-3 rounded-row px-3 text-body transition-colors',
                isActive
                  ? 'bg-accent-tint font-semibold text-accent-ink'
                  : 'text-ink-2 hover:bg-surface-2 hover:text-ink',
              )
            }
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 3" />
            </svg>
            Past sims
          </NavLink>
        </nav>
        <div className="mt-auto flex flex-col gap-1.5 px-3">
          {sampleMode && (
            <>
              <p className="text-caption text-muted">Viewing sample data</p>
              <button
                type="button"
                className={cx(INTERACTIVE, 'btn-primary press rounded-row px-3 py-2 text-subhead')}
                onClick={sampleMode.exit}
              >
                Sign in
              </button>
            </>
          )}
          {session && (
            <>
              <p className="truncate text-caption text-muted" title={session.email}>
                Signed in as {session.email}
              </p>
              <button
                type="button"
                className={cx(
                  INTERACTIVE,
                  'self-start rounded-chip text-caption text-ink-2 underline',
                )}
                onClick={() => void session.signOut()}
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
