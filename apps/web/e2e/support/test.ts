import { test as base, expect, type Page } from '@playwright/test'
import { API_URL } from './urls'

export { expect }

/** Every route of the app, in tab order. */
export const ROUTES = ['/today', '/matchup', '/waivers', '/players', '/ask'] as const
export const TABS = ['Today', 'Matchup', 'Waivers', 'Players', 'Ask'] as const

/** WEB-024: players are cards on phones and table rows from 840 px. */
export const playerRows = (page: Page) =>
  page
    .getByRole('list', { name: 'Players' })
    .getByRole('listitem')
    .or(page.getByRole('table', { name: 'Players' }).locator('tbody').getByRole('row'))

/** The player detail: a modal sheet, or from 1200 px a panel beside the table. */
export const playerDetail = (page: Page, name?: string) =>
  name
    ? page.getByRole('dialog', { name }).or(page.getByRole('complementary', { name }))
    : page.getByRole('dialog').or(page.locator('aside[aria-labelledby]'))

/** A badge or signal filter chip; from 840 px they sit in the Filters popover, opened first. */
export async function filterChip(page: Page, group: 'badge' | 'signal', name: string | RegExp) {
  const filters = page.getByRole('button', { name: 'Filters' })
  if ((await filters.count()) > 0 && (await filters.getAttribute('aria-expanded')) === 'false')
    await filters.click()
  return page.getByRole('group', { name: `Filter by ${group}` }).getByRole('button', { name })
}

export type Endpoint =
  'today' | 'matchup' | 'waivers' | 'players' | `replay/${string}` | `me/${string}`

/** One mocked API answer. `json` is the body; problems use RFC 9457 problem+json. */
export interface Reply {
  status?: number
  json?: unknown
  delayMs?: number
}
type Handler = Reply | ((url: URL) => Reply)

/** An RFC 9457 problem as the API sends it. */
export const problem = (status: number, type: string, title = 'raw title from the API'): Reply => ({
  status,
  json: { type: `/problems/${type}`, title, status },
})

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': 'authorization, accept',
  'access-control-allow-methods': 'GET, OPTIONS',
}

/**
 * Mocks the API host at the network layer (page.route). Endpoints left out answer as a route the
 * API doesn't have yet (404 not-found). Returns the paths the page requested, in order.
 */
export async function mockApi(page: Page, handlers: Partial<Record<Endpoint, Handler>>) {
  const calls: string[] = []
  const auth: (string | undefined)[] = []
  await page.route(`${API_URL}/**`, async (route) => {
    const req = route.request()
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: CORS })
    const url = new URL(req.url())
    calls.push(url.pathname + url.search)
    auth.push(req.headers()['authorization'])
    const h = handlers[url.pathname.slice(1) as Endpoint]
    const reply = (typeof h === 'function' ? h(url) : h) ?? problem(404, 'not-found', 'Not Found')
    if (reply.delayMs) await new Promise((r) => setTimeout(r, reply.delayMs))
    const status = reply.status ?? 200
    await route.fulfill({
      status,
      headers: {
        ...CORS,
        'content-type': status >= 400 ? 'application/problem+json' : 'application/json',
      },
      body: JSON.stringify(reply.json ?? {}),
    })
  })
  return { calls, auth }
}

/** Signs in through the e2e auth seam (src/auth/e2eAuth.ts) before the app loads. */
export async function signInAs(page: Page, email = 'owner@example.test') {
  await page.addInitScript((e) => window.localStorage.setItem('e2e-email', e), email)
}

/** No horizontal scroll: the page is no wider than the viewport. */
export async function overflowX(page: Page) {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
}

interface NetworkLog {
  /** Every http(s) host the page requested. */
  hosts: Set<string>
}

/**
 * The base test for every persona. It blocks the NBA headshot CDN (the avatars fall back to
 * initials, so runs never depend on it) and fails a test whose page talked to any host other than
 * the site under test, the mocked API, or that CDN — so no real Google, Firebase or API call
 * can slip through (AC2).
 */
export const test = base.extend<{ network: NetworkLog }>({
  network: [
    async ({ page, baseURL }, use) => {
      const hosts = new Set<string>()
      page.on('request', (r) => {
        const u = new URL(r.url())
        if (u.protocol === 'http:' || u.protocol === 'https:') hosts.add(u.host)
      })
      await page.route('https://cdn.nba.com/**', (r) => r.abort())
      await use({ hosts })
      const allowed = new Set([new URL(baseURL ?? '').host, new URL(API_URL).host, 'cdn.nba.com'])
      expect(
        [...hosts].filter((h) => !allowed.has(h)),
        'unmocked hosts',
      ).toEqual([])
    },
    { auto: true },
  ],
})
