import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { draftedLeague, replayWithGames } from '../src/features/replay/fixtures/replayWithGames'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, overflowX, problem, signInAs, test } from './support/test'

// Persona: the owner after a 2024-25 replay draft. "Let me play week 1: check the schedule, stream a
// pickup, bench someone, and see how it went." (SIM-004)

const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']

async function expectClean(page: Page, label: string) {
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze()
  const serious = violations
    .filter((v) => v.impact === 'serious' || v.impact === 'critical')
    .map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target.join(' ')) }))
  expect(serious, label).toEqual([])
}

test.describe('signed in, with a saved 2024-25 replay league', () => {
  test.use({ baseURL: LIVE_URL })

  test.beforeEach(async ({ page }) => {
    await signInAs(page)
    const league = draftedLeague()
    await page.addInitScript(
      (l) => window.localStorage.setItem('replay-league', l),
      JSON.stringify(league),
    )
    const doc = replayWithGames('2024-25')
    await mockApi(page, {
      today: problem(404, 'no-brief'),
      'replay/seasons': { json: { seasons: ['2024-25'] } },
      'replay/2024-25': { json: doc },
    })
  })

  test('plays a week: schedule, a pickup, a benching, then the result kept', async ({ page }) => {
    test.slow() // a full week on emulated WebKit
    await page.goto('/replay')
    await expect(page.getByRole('heading', { level: 1, name: 'Week 1 vs Team 2' })).toBeVisible()
    await expect(page.getByRole('table', { name: 'Your team’s week' })).toBeVisible()
    await expect(page.getByText(/Games by NBA team this week:/)).toBeVisible()
    let o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
    await expectClean(page, 'week view')

    await page
      .getByRole('list', { name: 'Free agents' })
      .getByRole('button', { name: /^Add / })
      .first()
      .click()
    await page
      .getByRole('group', { name: /^Pick up / })
      .getByRole('button', { name: 'Confirm' })
      .click()
    await expect(page.getByText('3 of 4')).toBeVisible()

    const mine = page.getByRole('table', { name: 'Your team’s week' })
    await mine
      .getByRole('button', { name: /starts\. Bench him$/ })
      .first()
      .click()
    await expect(mine.getByRole('button', { name: /benched by you\. Start him$/ })).toHaveCount(1)

    await page.getByRole('button', { name: 'Play the week' }).click()
    await expect(page.getByText(/^(Won|Lost|Tied) \d-\d-\d$/)).toBeVisible()
    await expect(page.getByRole('list', { name: 'Day by day' }).getByRole('listitem')).toHaveCount(
      6,
    )
    await expectClean(page, 'result')
    await page.getByRole('button', { name: 'Keep this result' }).click()
    await expect(page.getByText(/You kept/)).toBeVisible()
    o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
  })
})
