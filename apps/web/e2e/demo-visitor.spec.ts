import { API_URL, DEMO_URL } from './support/urls'
import { expect, playerRows, ROUTES, test } from './support/test'

// Persona: a demo visitor on the public sample build, not signed in. "What is this? Show me."
test.use({ baseURL: DEMO_URL })

test('every tab renders the sample data, with no sign-in', async ({ page }) => {
  for (const route of ROUTES) {
    await page.goto(route)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expect(page.getByText('Sample data')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in with Google' })).toHaveCount(0)
    await expect(page.getByRole('alert')).toHaveCount(0)
  }
  // The sample brief itself is on screen, not an empty state.
  await page.goto('/today')
  await expect(page.getByRole('table', { name: /projected category results/i })).toBeVisible()
  await page.goto('/waivers')
  await expect(page.getByText('Jalen Smith')).toBeVisible()
})

test('the root opens Today', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/today$/)
})

test('a deep link to a player search works on first load', async ({ page }) => {
  await page.goto('/players?q=jok')
  await expect(page.getByRole('searchbox', { name: 'Search players' })).toHaveValue('jok')
  await expect(playerRows(page)).toHaveCount(1)
  await expect(playerRows(page)).toContainText('Nikola Jokić')
  await expect(page.getByText('1 of 10 players')).toBeVisible()
})

test('no request leaves for the API, Google or Firebase', async ({ page, network }) => {
  for (const route of ROUTES) {
    await page.goto(route)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  }
  const hosts = [...network.hosts]
  expect(hosts).not.toContain(new URL(API_URL).host)
  expect(hosts.filter((h) => /google|firebase|gstatic/.test(h))).toEqual([])
  expect(hosts.filter((h) => h !== new URL(DEMO_URL).host && h !== 'cdn.nba.com')).toEqual([])
})
