import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Suspense, lazy, useState } from 'react'
import {
  Navigate,
  Outlet,
  RouterProvider,
  createBrowserRouter,
  createMemoryRouter,
  useLocation,
  type RouteObject,
} from 'react-router'
import { ApiProvider } from './api/client'
import { defaultAuth, defaultClient, liveApiUrl } from './api/select'
import type { ApiClient } from './api/types'
import {
  SampleModeContext,
  SignInGate,
  useSampleMode,
  useSession,
  type AuthAdapter,
} from './auth/auth'
import { fixtureClient } from './api/fixtures'
import { INTERACTIVE, cx } from './components/ui/interactive'
import { NotFoundPage, RouteCrash } from './components/ui/PageStates'
import { Sidebar } from './components/ui/Sidebar'
import { TabBar } from './components/ui/TabBar'
import { EXPANDED, useMediaQuery } from './components/ui/useMediaQuery'
import { AskPage } from './features/ask/AskPage'
import { PracticeHub } from './features/practice/PracticeHub'
import { ReplayPage } from './features/replay/ReplayPage'
import { PastSimsPage, SimDetailPage } from './features/sims/PastSimsPage'
import { MatchupPage } from './features/matchup/MatchupPage'
import { PlayersPage } from './features/players/PlayersPage'
import { TodayPage } from './features/today/TodayPage'
import { WaiversPage } from './features/waivers/WaiversPage'

const DraftPracticePage = lazy(() =>
  import('./features/draft/DraftPracticePage').then((m) => ({ default: m.DraftPracticePage })),
)

/** Routes that use the full 1200 px content width; the rest keep a 760 px reading column (§9). */
const WIDE = new Set(['/players', '/today', '/draft', '/replay'])

function Shell() {
  const session = useSession()
  const sampleMode = useSampleMode()
  const desktop = useMediaQuery(EXPANDED)
  const { pathname } = useLocation()
  // One tree for every width (WEB-028): <main> keeps its position, so crossing 840 px swaps only the
  // navigation around it and the routed page keeps its state.
  return (
    <div
      className={
        desktop
          ? 'grid min-h-dvh grid-cols-[240px_1fr] bg-ground'
          : 'mx-auto flex min-h-svh max-w-md flex-col bg-ground'
      }
    >
      {desktop ? <Sidebar /> : null}
      <main className={desktop ? 'min-w-0 px-8 pb-12' : 'flex-1'}>
        <div
          className={
            desktop
              ? cx('mx-auto', WIDE.has(pathname) ? 'max-w-[1200px]' : 'max-w-[760px]')
              : undefined
          }
        >
          <Outlet />
        </div>
      </main>
      {!desktop && sampleMode && (
        <p className="px-5 pb-2 text-caption text-muted">
          Viewing sample data ·{' '}
          <button
            type="button"
            className={cx(INTERACTIVE, 'rounded-chip underline')}
            onClick={sampleMode.exit}
          >
            Sign in
          </button>
        </p>
      )}
      {!desktop && session && (
        <p className="px-5 pb-2 text-caption text-muted">
          Signed in as {session.email} ·{' '}
          <button
            type="button"
            className={cx(INTERACTIVE, 'rounded-chip underline')}
            onClick={() => void session.signOut()}
          >
            Sign out
          </button>
        </p>
      )}
      {!desktop && (
        <div className="sticky bottom-0 z-10">
          <TabBar />
        </div>
      )}
    </div>
  )
}

export const routes: RouteObject[] = [
  {
    element: <Shell />,
    children: [
      { index: true, element: <Navigate to="/today" replace /> },
      { path: 'today', element: <TodayPage />, errorElement: <RouteCrash /> },
      { path: 'matchup', element: <MatchupPage />, errorElement: <RouteCrash /> },
      { path: 'waivers', element: <WaiversPage />, errorElement: <RouteCrash /> },
      { path: 'players', element: <PlayersPage />, errorElement: <RouteCrash /> },
      { path: 'ask', element: <AskPage />, errorElement: <RouteCrash /> },
      {
        path: 'draft',
        element: (
          <Suspense
            fallback={<p className="p-5 text-subhead text-muted">Loading the draft room…</p>}
          >
            <DraftPracticePage />
          </Suspense>
        ),
        errorElement: <RouteCrash />,
      },
      { path: 'practice', element: <PracticeHub />, errorElement: <RouteCrash /> },
      { path: 'replay', element: <ReplayPage />, errorElement: <RouteCrash /> },
      { path: 'sims', element: <PastSimsPage />, errorElement: <RouteCrash /> },
      { path: 'sims/:id', element: <SimDetailPage />, errorElement: <RouteCrash /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]

// WEB-026: a signed-out visitor can explore the sample fixtures inside the live build, per tab.
const SAMPLE_KEY = 'sample-mode'
function readSampleMode(): boolean {
  try {
    return sessionStorage.getItem(SAMPLE_KEY) === '1'
  } catch {
    return false
  }
}

/** `initialPath` switches to an in-memory router (tests); the app uses the browser URL. */
export function App({
  client = defaultClient,
  sample = liveApiUrl === null,
  auth = defaultAuth,
  initialPath,
}: {
  client?: ApiClient
  sample?: boolean
  /** Live mode's sign-in (D-27); null in demo mode. */
  auth?: AuthAdapter | null
  initialPath?: string
}) {
  const [router] = useState(() =>
    initialPath
      ? createMemoryRouter(routes, { initialEntries: [initialPath] })
      : createBrowserRouter(routes),
  )
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: false } } }))
  const [exploring, setExploring] = useState(readSampleMode)
  const explore = (on: boolean) => {
    try {
      if (on) sessionStorage.setItem(SAMPLE_KEY, '1')
      else sessionStorage.removeItem(SAMPLE_KEY)
    } catch {
      // storage blocked: sample mode just won't survive a refresh
    }
    qc.clear() // never show sample answers as live ones, or the reverse
    setExploring(on)
  }
  if (auth && exploring)
    return (
      <QueryClientProvider client={qc}>
        <ApiProvider client={fixtureClient} sample>
          <SampleModeContext.Provider value={{ exit: () => explore(false) }}>
            <RouterProvider router={router} />
          </SampleModeContext.Provider>
        </ApiProvider>
      </QueryClientProvider>
    )
  return (
    <QueryClientProvider client={qc}>
      <ApiProvider client={client} sample={sample}>
        {auth ? (
          <SignInGate adapter={auth} onExplore={() => explore(true)}>
            <RouterProvider router={router} />
          </SignInGate>
        ) : (
          <RouterProvider router={router} />
        )}
      </ApiProvider>
    </QueryClientProvider>
  )
}
