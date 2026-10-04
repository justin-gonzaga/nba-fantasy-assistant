import { LIVE_URL } from './support/urls'
import { expect, mockApi, problem, signInAs, test } from './support/test'

// Persona: someone signed in with a Google account that isn't invited. "Why can't I see anything?"
test.use({ baseURL: LIVE_URL })

const STRANGER = 'stranger@example.test'
const NO_ACCESS = 'This account doesn’t have access'

test.beforeEach(async ({ page }) => {
  await signInAs(page, STRANGER)
  const forbidden = problem(403, 'forbidden', 'Forbidden')
  await mockApi(page, {
    today: forbidden,
    matchup: forbidden,
    waivers: forbidden,
    players: forbidden,
  })
})

for (const route of ['/today', '/matchup', '/waivers', '/players']) {
  test(`${route}: a clear no-access screen with Sign out, and no data`, async ({ page }) => {
    await page.goto(route)
    const card = page.getByRole('alert').filter({ hasText: NO_ACCESS })
    await expect(card).toBeVisible()
    await expect(card).toContainText('Sign out and use an invited account.')
    await expect(card).toContainText(`Signed in as ${STRANGER}.`)
    await expect(page.getByText('Forbidden')).toHaveCount(0) // the API's raw title never shows
    await expect(page.getByRole('table')).toHaveCount(0)
    await expect(page.getByRole('list', { name: 'Players' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Retry' })).toHaveCount(0)
  })
}

test('the Ask tab shows no data either', async ({ page }) => {
  await page.goto('/ask')
  await expect(page.getByText('Coming soon')).toBeVisible()
  await expect(page.getByText('Sample data')).toHaveCount(0)
})

test('Sign out returns to the sign-in screen', async ({ page }) => {
  await page.goto('/today')
  const card = page.locator('.surface').filter({ hasText: NO_ACCESS })
  await card.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible()
  await expect(page.getByText(NO_ACCESS)).toHaveCount(0)
  await expect(page.getByText(STRANGER)).toHaveCount(0)
})
