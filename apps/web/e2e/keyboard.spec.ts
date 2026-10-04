import { DEMO_URL } from './support/urls'
import { expect, playerDetail, TABS, test } from './support/test'

// Persona: a keyboard-only user (Tab, Enter, Escape). The real sheet motion stays on here.
test.use({ baseURL: DEMO_URL, contextOptions: { reducedMotion: 'no-preference' } })

/** Presses Tab until `done` holds for the focused element, or gives up after `max` presses. */
async function tabUntil(
  page: import('@playwright/test').Page,
  done: () => Promise<boolean>,
  max = 40,
): Promise<boolean> {
  for (let i = 0; i < max; i++) {
    await page.keyboard.press('Tab')
    if (await done()) return true
  }
  return false
}

test('Tab reaches every tab link, and Enter follows it', async ({ page, browserName }) => {
  // Safari's Tab skips links unless the user turns on "Press Tab to highlight each item".
  test.skip(browserName === 'webkit', 'WebKit tabs to links only with a Safari setting')
  await page.goto('/today')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  const nav = page.getByRole('navigation', { name: 'Main' })
  for (const tab of TABS) {
    const link = nav.getByRole('link', { name: tab })
    const reached = await tabUntil(page, () => link.evaluate((el) => el === document.activeElement))
    expect(reached, `Tab reaches ${tab}`).toBe(true)
  }
  // Shift+Tab back from Ask to Matchup, then Enter opens it.
  for (let i = 0; i < 3; i++) await page.keyboard.press('Shift+Tab')
  await expect(nav.getByRole('link', { name: 'Matchup' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/matchup$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Matchup' })).toBeVisible()
})

test('a player opens with Enter and closes with Escape, focus returning to the row', async ({
  page,
}) => {
  await page.goto('/players')
  const row = page.getByRole('button', { name: /Victor Wembanyama/ })
  await expect(row).toBeVisible()
  const reached = await tabUntil(page, () => row.evaluate((el) => el === document.activeElement))
  expect(reached, 'Tab reaches the player row').toBe(true)

  await page.keyboard.press('Enter')
  const sheet = playerDetail(page, 'Victor Wembanyama')
  await expect(sheet).toBeVisible()
  // Focus moves into the sheet (its Close button) and Tab stays inside.
  await expect(sheet.getByRole('button', { name: 'Close' })).toBeFocused()
  await page.keyboard.press('Tab')
  await page.keyboard.press('Shift+Tab')
  expect(await sheet.evaluate((el) => el.contains(document.activeElement))).toBe(true)

  await page.keyboard.press('Escape')
  await expect(sheet).toHaveCount(0)
  await expect(row).toBeFocused()
})

test('the Close button works from the keyboard too', async ({ page }) => {
  await page.goto('/players')
  const row = page.getByRole('button', { name: /Nikola Jokić/ })
  await row.focus()
  await page.keyboard.press('Enter')
  const close = playerDetail(page).getByRole('button', { name: 'Close' })
  await expect(close).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(playerDetail(page)).toHaveCount(0)
  await expect(row).toBeFocused()
})
