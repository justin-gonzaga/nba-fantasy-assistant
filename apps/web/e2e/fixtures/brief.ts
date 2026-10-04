import { sampleMatchup, sampleToday, sampleWaivers } from '../../src/api/fixtures'
import type { Freshness, Matchup, Today, Waivers } from '../../src/api/types'

// WEB-008: in-season API payloads (the app's SAMPLE brief, typed against the API contract) and the
// same brief on a day the NBA update didn't run (WEB-016 StaleNotice).

export const inSeason = { today: sampleToday, matchup: sampleMatchup, waivers: sampleWaivers }

const stale: Freshness = {
  asOf: '2026-10-20T09:42:00+11:00',
  staleSince: '2026-10-20',
  sources: [{ name: 'Injury report', asOf: '2026-10-20T09:30:00+11:00' }],
}
const staleMatchup: Matchup = { ...sampleMatchup, freshness: stale }
const staleToday: Today = { ...sampleToday, matchup: staleMatchup, freshness: stale }
const staleWaivers: Waivers = { ...sampleWaivers, freshness: stale }

export const staleDay = { today: staleToday, matchup: staleMatchup, waivers: staleWaivers }
export const STALE_TITLE = 'Data from Tue 20 Oct'
