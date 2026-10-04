import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, type ReactNode } from 'react'
import { fixtureClient } from './fixtures'
import type { ApiClient } from './types'

// The only place pages get data from. APP-003 swaps the fixture client for the generated one.
const ApiContext = createContext<ApiClient>(fixtureClient)
const SampleContext = createContext(true)

export function ApiProvider({
  client,
  sample,
  children,
}: {
  client: ApiClient
  sample: boolean
  children: ReactNode
}) {
  return (
    <ApiContext.Provider value={client}>
      <SampleContext.Provider value={sample}>{children}</SampleContext.Provider>
    </ApiContext.Provider>
  )
}

/** True when pages show the sample data (demo mode), not the live API. */
export function useIsSample(): boolean {
  return useContext(SampleContext)
}

function useApi(): ApiClient {
  return useContext(ApiContext)
}

export function useToday() {
  const api = useApi()
  return useQuery({ queryKey: ['today'], queryFn: () => api.today() })
}

export function useMatchup() {
  const api = useApi()
  return useQuery({ queryKey: ['matchup'], queryFn: () => api.matchup() })
}

export function useWaivers() {
  const api = useApi()
  return useQuery({ queryKey: ['waivers'], queryFn: () => api.waivers() })
}

/** Keeps the previous strategy's list on screen while another strategy loads. */
export function usePlayers(variant: string) {
  const api = useApi()
  return useQuery({
    queryKey: ['players', variant],
    queryFn: () => api.players(variant),
    placeholderData: keepPreviousData,
  })
}

/** SIM-002: which past seasons can be replayed (none on a client without replay, e.g. the demo). */
export function useReplaySeasons() {
  const api = useApi()
  return useQuery({
    queryKey: ['replay-seasons'],
    queryFn: () => (api.replaySeasons ? api.replaySeasons() : Promise.resolve({ seasons: [] })),
  })
}

/** SIM-002/004: a season's replay file; fetched only when `season` is set. Immutable once published. */
export function useReplaySeason(season: string | null) {
  const api = useApi()
  return useQuery({
    queryKey: ['replay', season],
    queryFn: () => {
      if (!season || !api.replaySeason) throw new Error('No replay for this season')
      return api.replaySeason(season)
    },
    enabled: season !== null,
    staleTime: Infinity,
  })
}

/** Loads a season's replay file on demand (e.g. when a replay draft starts), sharing the hook's cache. */
export function useReplayLoader(): (season: string) => Promise<unknown> {
  const api = useApi()
  const qc = useQueryClient()
  return (season) =>
    qc.fetchQuery({
      queryKey: ['replay', season],
      queryFn: () => {
        if (!api.replaySeason) throw new Error('No replay for this season')
        return api.replaySeason(season)
      },
      staleTime: Infinity,
    })
}

/** SIM-006: the signed-in user's saved sims (none on a client without an account, e.g. the demo). */
export function useSims() {
  const api = useApi()
  return useQuery({
    queryKey: ['sims'],
    queryFn: () => (api.sims ? api.sims.list() : Promise.resolve([])),
  })
}

/** The sims API for actions (save, pin, delete…), or undefined without an account; `refresh` re-reads the list. */
export function useSimsApi() {
  const api = useApi()
  const qc = useQueryClient()
  return {
    sims: api.sims,
    refresh: () => qc.invalidateQueries({ queryKey: ['sims'] }),
  }
}

/** One saved sim with its full detail (SIM-006 reopen). */
export function useSim(id: string) {
  const api = useApi()
  return useQuery({
    queryKey: ['sim', id],
    queryFn: async () => {
      if (!api.sims) throw new Error('Sign in to see your saved sims')
      return (await api.sims.get(id)).sim
    },
  })
}
