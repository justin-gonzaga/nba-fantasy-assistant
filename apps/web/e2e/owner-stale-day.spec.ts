import { STALE_TITLE, staleDay } from './fixtures/brief'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, signInAs, test } from './support/test'

// Persona: the owner on a day the PC didn't fetch the NBA data. "Can I trust this?"
test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page }) => {
  await signInAs(page)
  await mockApi(page, {
    today: { json: staleDay.today },
    matchup: { json: staleDay.matchup },
    waivers: { json: staleDay.waivers },
  })
})

for (const route of ['/today', '/matchup', '/waivers']) {
  test(`${route} says which day the data is from, and nothing claims to be live`, async ({
    page,
  }) => {
    await page.goto(route)
    const notice = page.getByRole('status').filter({ hasText: STALE_TITLE })
    await expect(notice).toBeVisible()
    await expect(notice).toContainText('Today’s NBA update didn’t run')
    // The notice sits above the data, and the footer dates the data to that day too.
    await expect(page.getByText(/Updated .* · injury report/)).toBeVisible()
    await expect(page.locator('main')).not.toContainText(/\blive\b|just now/i)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
}
