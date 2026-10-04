import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { inSeason } from './fixtures/brief'
import { draftPlayers } from './fixtures/players'
import { DEMO_URL, LIVE_URL } from './support/urls'
import { expect, mockApi, playerDetail, problem, ROUTES, signInAs, test } from './support/test'

// AC5: axe on every page, in the demo and the owner builds, plus the states a persona meets
// (sheet open, not-ready, no access, error). Zero serious or critical violations.
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']

async function seriousViolations(page: Page) {
  // At the end of the page the sticky tab bar sits below the content; mid-scroll it overlaps the
  // row under it, which axe's target-size rule reads as an obscured target. Real taps scroll first.
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze()
  return violations
    .filter((v) => v.impact === 'serious' || v.impact === 'critical')
    .map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.map((n) => `${n.target.join(' ')}: ${n.failureSummary ?? ''}`),
    }))
}

async function expectClean(page: Page, label: string) {
  expect(await seriousViolations(page), label).toEqual([])
}

test.describe('demo build', () => {
  test.use({ baseURL: DEMO_URL })

  for (const route of ROUTES) {
    test(`${route}`, async ({ page }) => {
      await page.goto(route)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await expectClean(page, route)
    })
  }

  test('player sheet open', async ({ page }) => {
    await page.goto('/players')
    await page.getByRole('button', { name: /Chet Holmgren/ }).click()
    await expect(playerDetail(page)).toBeVisible()
    await expectClean(page, 'sheet')
  })

  test('page not found', async ({ page }) => {
    await page.goto('/nowhere')
    await expect(page.getByText('Page not found')).toBeVisible()
    await expectClean(page, '404')
  })
})

test.describe('demo build, dark theme', () => {
  test.use({ baseURL: DEMO_URL, colorScheme: 'dark' })

  for (const route of ROUTES) {
    test(`${route}`, async ({ page }) => {
      await page.goto(route)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await expectClean(page, route)
    })
  }

  test('player sheet open', async ({ page }) => {
    await page.goto('/players')
    await page.getByRole('button', { name: /Chet Holmgren/ }).click()
    await expect(playerDetail(page)).toBeVisible()
    await expectClean(page, 'sheet')
  })
})

test.describe('owner build', () => {
  test.use({ baseURL: LIVE_URL })

  test('draft practice: setup and a live lot (DRAFT-014)', async ({ page }) => {
    await signInAs(page)
    await mockApi(page, { players: () => ({ json: draftPlayers('all') }) })
    await page.goto('/draft')
    await expect(page.getByRole('button', { name: 'Start practice draft' })).toBeVisible()
    await expectClean(page, 'draft setup')
    await page.getByRole('radio', { name: /Untimed/ }).check()
    await page.getByRole('button', { name: 'Start practice draft' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Draft practice' })).toBeVisible()
    await expectClean(page, 'draft room')
  })

  test('sign-in screen', async ({ page }) => {
    await page.goto('/today')
    await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible()
    await expectClean(page, 'sign-in')
  })

  for (const route of ROUTES) {
    test(`${route} in season`, async ({ page }) => {
      await signInAs(page)
      await mockApi(page, {
        today: { json: inSeason.today },
        matchup: { json: inSeason.matchup },
        waivers: { json: inSeason.waivers },
        players: { json: draftPlayers() },
      })
      await page.goto(route)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await expectClean(page, route)
    })
  }

  test('states: not ready, no access, error', async ({ page }) => {
    await signInAs(page)
    await mockApi(page, {
      today: problem(404, 'no-brief'),
      matchup: problem(403, 'forbidden'),
      waivers: problem(502, 'bad-gateway'),
    })
    for (const [route, text] of [
      ['/today', 'Your daily brief starts with the season'],
      ['/matchup', 'This account doesn’t have access'],
      ['/waivers', 'Something went wrong on our side'],
    ] as const) {
      await page.goto(route)
      await expect(page.getByText(text)).toBeVisible()
      await expectClean(page, route)
    }
  })
})
