import { inSeason } from './fixtures/brief'
import { draftPlayers } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, playerRows, problem, signInAs, test, type Reply } from './support/test'

// Persona: the owner when the API is down, slow, or behind the site. "Is it broken?"
test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page }) => {
  await signInAs(page)
})

/** Fails with `first` until the page retries, then answers `then`. */
function failOnce(first: Reply, then: Reply) {
  let n = 0
  return () => (n++ === 0 ? first : then)
}

test('a 502 shows an error with Retry, and Retry recovers', async ({ page }) => {
  await mockApi(page, {
    today: failOnce(problem(502, 'bad-gateway', 'Bad Gateway'), { json: inSeason.today }),
  })
  await page.goto('/today')
  const card = page.getByRole('alert').filter({ hasText: 'Something went wrong on our side' })
  await expect(card).toBeVisible()
  await expect(page.getByText('Bad Gateway')).toHaveCount(0)
  await page.getByRole('button', { name: 'Retry' }).click()
  await expect(page.getByRole('heading', { level: 1, name: '5–3–1' })).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('Players recovers from a 502 too', async ({ page }) => {
  await mockApi(page, {
    players: failOnce(problem(502, 'bad-gateway'), { json: draftPlayers() }),
  })
  await page.goto('/players')
  await page.getByRole('button', { name: 'Retry' }).click()
  await expect(playerRows(page).first()).toBeVisible()
})

test('a slow (3 s) answer shows loading, never a blank page', async ({ page }) => {
  await mockApi(page, { matchup: { json: inSeason.matchup, delayMs: 3000 } })
  await page.goto('/matchup')
  const loading = page.getByRole('status').filter({ hasText: 'Loading…' })
  await expect(loading).toBeAttached()
  await expect(page.getByRole('navigation', { name: 'Main' })).toBeVisible()
  await page.waitForTimeout(1500) // still waiting: still loading, still not blank
  await expect(loading).toBeAttached()
  await expect(page.getByRole('heading', { level: 1, name: 'Matchup' })).toBeVisible({
    timeout: 10_000,
  })
  await expect(loading).toHaveCount(0)
})

test('a route the API doesn’t have yet (site ahead of API) says it is being updated', async ({
  page,
}) => {
  await mockApi(page, {}) // every endpoint 404 not-found
  for (const route of ['/today', '/waivers', '/players']) {
    await page.goto(route)
    await expect(page.getByText('This part is being updated')).toBeVisible()
    await expect(page.getByText('Try again in a few minutes.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible()
  }
})
