import { API_URL, LIVE_URL } from './support/urls'
import { expect, overflowX, test } from './support/test'

// Persona: a visitor who isn't signed in. "What is this, and can I look around first?" (WEB-026)
test.use({ baseURL: LIVE_URL })

test('the landing explains the app and offers both ways in, without sideways scroll', async ({
  page,
}) => {
  await page.goto('/today')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Explore with sample data' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'How it works' })).toBeVisible()
  const o = await overflowX(page)
  expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
})

test('exploring the sample makes no API calls, and Sign in returns to the landing', async ({
  page,
}) => {
  const api: string[] = []
  page.on('request', (r) => {
    if (r.url().startsWith(API_URL)) api.push(r.url())
  })
  await page.goto('/today')
  await page.getByRole('button', { name: 'Explore with sample data' }).click()
  await expect(page.getByRole('table', { name: /projected category results/i })).toBeVisible()
  await expect(page.getByText('Sample data').first()).toBeVisible()
  await page.goto('/players') // a refresh keeps sample mode for the tab
  await expect(page.getByRole('heading', { level: 1, name: 'Players' })).toBeVisible()
  expect(api).toEqual([])
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible()
})
