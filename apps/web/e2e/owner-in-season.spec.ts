import { inSeason } from './fixtures/brief'
import { draftPlayers } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, playerRows, signInAs, test } from './support/test'

// Persona: the owner mid-season on the live build. "What do I do today? Who should I pick up?"
test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page }) => {
  await signInAs(page)
  await mockApi(page, {
    today: { json: inSeason.today },
    matchup: { json: inSeason.matchup },
    waivers: { json: inSeason.waivers },
    players: { json: draftPlayers() },
  })
})

test('Today: the scoreboard, then actions that expand to their why', async ({ page }) => {
  await page.goto('/today')
  await expect(page.getByRole('heading', { level: 1, name: '5–3–1' })).toBeVisible()
  await expect(page.getByText('Sample data')).toHaveCount(0)
  const action = page.getByRole('button', { name: /Start Keegan Murray over Harrison Barnes/ })
  await expect(action).toHaveAttribute('aria-expanded', 'false')
  await action.click()
  await expect(action).toHaveAttribute('aria-expanded', 'true')
  await expect(page.getByText('A player without a game scores nothing today.')).toBeVisible()
  await expect(page.getByText('Confidence: high · Locks 7:00 pm')).toBeVisible()
  await action.click()
  await expect(page.getByText('A player without a game scores nothing today.')).toHaveCount(0)
})

test('Matchup: all nine categories; a tap shows what moves one', async ({ page }) => {
  await page.goto('/matchup')
  await expect(page.getByRole('heading', { level: 1, name: 'Matchup' })).toBeVisible()
  const cats = page.getByRole('listitem').filter({ has: page.getByRole('button') })
  await expect(cats).toHaveCount(9)
  await expect(page.getByText('5.2 of 9')).toBeVisible()
  await page.getByRole('button', { name: /^REB/ }).click()
  await expect(page.getByText('Streaming a big lifts this to about 45%.')).toBeVisible()
})

test('Waivers: the category filter narrows the pickups', async ({ page }) => {
  await page.goto('/waivers')
  const list = page.getByRole('main').getByRole('list')
  await expect(list.getByRole('listitem')).toHaveCount(6)
  await page.getByRole('button', { name: 'BLK', exact: true }).click()
  await expect(page.getByRole('button', { name: 'BLK', exact: true })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await expect(list.getByRole('listitem')).toHaveCount(2)
  await expect(list).toContainText('Jalen Smith')
  await expect(list).not.toContainText('Ayo Dosunmu')
  await page.getByRole('button', { name: 'STL', exact: true }).click()
  await expect(list.getByRole('listitem')).toHaveCount(2)
  await expect(list).toContainText('Ayo Dosunmu')
  await expect(page.getByText('Suggested drop: Cody Martin.')).toBeVisible()
})

test('Players: today’s injury status shows as a badge on the row', async ({ page }) => {
  await page.goto('/players')
  const row = (name: string) => playerRows(page).filter({ hasText: name })
  await expect(row('Giannis Antetokounmpo').getByText('Questionable')).toBeVisible()
  await expect(row('Domantas Sabonis').getByText('Out', { exact: true })).toBeVisible()
  await expect(row('Nikola Jokić').getByText('Top tier')).toBeVisible()
})
