import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, overflowX, problem, signInAs, test } from './support/test'

// Persona: the owner the week before the auction. "Which strategy has done best in my practice runs?" (SIM-006)

const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']

async function expectClean(page: Page, label: string) {
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze()
  const serious = violations
    .filter((v) => v.impact === 'serious' || v.impact === 'critical')
    .map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target.join(' ')) }))
  expect(serious, label).toEqual([])
}

const summary = (i: number, title: string, surplus: number, wins: number) => ({
  id: `run-${i}`,
  kind: 'practice',
  season: '2026-27',
  title,
  summary: { surplus, categoryWins: wins, counted: 9, at: `2026-10-0${i}` },
  pinned: i === 2,
  hasDetail: false,
  createdAt: `2026-10-0${i}T09:00:00Z`,
  updatedAt: `2026-10-0${i}T09:00:00Z`,
  version: 1,
})

test.describe('signed in, with saved sims', () => {
  test.use({ baseURL: LIVE_URL })

  test.beforeEach(async ({ page }) => {
    await signInAs(page)
    const runs = [
      summary(3, 'All categories', 3, 4.8),
      summary(2, 'Punt FT%', 9, 5.2),
      summary(1, 'All categories', -4, 4.1),
    ]
    await mockApi(page, {
      today: problem(404, 'no-brief'),
      'me/sims': { json: runs },
      'me/sims/run-2': { json: { ...runs[1], detail: null } },
    })
  })

  test('compares runs, then reopens one', async ({ page }) => {
    await page.goto('/sims')
    const list = page.getByRole('list', { name: 'Your practice drafts' })
    await expect(list.getByRole('listitem')).toHaveCount(3)
    await expect(page.getByRole('img', { name: /Surplus over your last 3 runs/ })).toBeVisible()
    const o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
    await expectClean(page, 'list')

    await page.getByRole('combobox', { name: 'Sort' }).selectOption('surplus')
    await expect(list.getByRole('listitem').first()).toContainText('Punt FT%')
    await list.getByRole('listitem').first().getByRole('link', { name: 'Open' }).click()
    await expect(page.getByText(/Only the summary is kept for this run/)).toBeVisible()
    await expectClean(page, 'detail')
  })
})
