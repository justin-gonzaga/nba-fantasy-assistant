import { PLAYER_COUNT, draftPlayers } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, playerDetail, playerRows, problem, signInAs, test } from './support/test'

// Persona: the owner before the season, signed in on the live build.
// "Find what Wembanyama is worth; compare punting assists."
test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page }) => {
  await signInAs(page)
})

const preSeason = {
  today: problem(404, 'no-brief'),
  matchup: problem(404, 'no-brief'),
  waivers: problem(404, 'no-brief'),
  players: (url: URL) => ({ json: draftPlayers(url.searchParams.get('variant') ?? 'all') }),
}

test('finds Wembanyama in the full player pool and opens his value', async ({ page }) => {
  const api = await mockApi(page, preSeason)
  await page.goto('/players')
  await expect(page.getByText(`${PLAYER_COUNT} players`)).toBeVisible()
  await expect(page.getByText('Sample data')).toHaveCount(0)
  await expect(page.getByText('Signed in as owner@example.test')).toBeVisible()

  await page.getByRole('searchbox', { name: 'Search players' }).fill('wemb')
  await expect(page.getByText(`1 of ${PLAYER_COUNT} players`)).toBeVisible()
  await page.getByRole('button', { name: /Victor Wembanyama/ }).click()
  const sheet = playerDetail(page, 'Victor Wembanyama')
  await expect(sheet).toBeVisible()
  await expect(sheet.getByText('$66')).toBeVisible()
  await expect(sheet.getByText('#2', { exact: true })).toBeVisible()
  await expect(sheet.getByText('All categories')).toBeVisible()

  // Every call carried the signed-in token from the auth seam.
  expect(api.auth.every((a) => a === 'Bearer e2e-token:owner@example.test')).toBe(true)
})

test('compares punting assists: the API re-ranks and the URL keeps it', async ({ page }) => {
  const api = await mockApi(page, preSeason)
  await page.goto('/players')
  const first = playerRows(page).first()
  await expect(first).toContainText('Nikola Jokić')

  await page.getByRole('combobox', { name: 'Strategy' }).selectOption('punt_ast')
  await expect(page).toHaveURL(/variant=punt_ast/)
  const expected = draftPlayers('punt_ast').players[0]?.name ?? ''
  await expect(first).toContainText(expected)
  expect(api.calls).toContain('/players?variant=punt_ast')

  await page.reload()
  await expect(page.getByRole('combobox', { name: 'Strategy' })).toHaveValue('punt_ast')
})

test('Today and Matchup show the friendly "no brief yet" state, not an error', async ({ page }) => {
  await mockApi(page, preSeason)
  for (const [route, title] of [
    ['/today', 'Your daily brief starts with the season'],
    ['/matchup', 'Your matchup appears once the season starts'],
    ['/waivers', 'Waiver picks start with the season'],
  ] as const) {
    await page.goto(route)
    await expect(page.getByText(title)).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Retry' })).toHaveCount(0)
  }
})
