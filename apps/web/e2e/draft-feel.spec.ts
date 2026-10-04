import { draftPlayers } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, overflowX, problem, signInAs, test } from './support/test'

// DRAFT-020: the room's motion. Reduced motion must leave nothing running; the same lot with motion on
// must animate (so the check above is not vacuous).

test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page }) => {
  await signInAs(page)
  await mockApi(page, {
    today: problem(404, 'no-brief'),
    players: () => ({ json: draftPlayers('all') }),
  })
})

async function enterRoom(page: import('@playwright/test').Page) {
  await page.goto('/draft')
  await page.getByRole('radio', { name: /Real timers/ }).check()
  await page.getByRole('button', { name: 'Start practice draft' }).click()
  await expect(page.getByTestId('clock-ring')).toBeVisible()
}

async function playOneLot(page: import('@playwright/test').Page) {
  const pass = page.getByRole('button', { name: 'Pass' })
  if (await pass.isVisible()) await pass.click()
  else await page.getByRole('list', { name: 'Your targets' }).getByRole('button').first().click()
}

const running = (page: import('@playwright/test').Page) =>
  page.evaluate(() => document.getAnimations().length)

test.describe('reduced motion', () => {
  test.use({ contextOptions: { reducedMotion: 'reduce' } })

  test('reduced motion has no running animations', async ({ page }) => {
    await enterRoom(page)
    await page.waitForTimeout(700)
    expect(await running(page)).toBe(0)
    await playOneLot(page)
    await page.waitForTimeout(700)
    expect(await running(page)).toBe(0)
    const o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
  })
})

test.describe('motion allowed', () => {
  test.use({ contextOptions: { reducedMotion: 'no-preference' } })

  test('a new lot animates in, and the room still fits the screen', async ({ page }) => {
    await enterRoom(page)
    expect(await running(page)).toBeGreaterThan(0)
    const o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
  })
})
