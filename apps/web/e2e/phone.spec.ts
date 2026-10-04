import { inSeason } from './fixtures/brief'
import { draftPlayers } from './fixtures/players'
import { DEMO_URL, LIVE_URL } from './support/urls'
import { ROUTES, TABS, expect, mockApi, overflowX, signInAs, test } from './support/test'

// Persona: one-handed phone use. Every route at 375–412 px (iPhone SE/mini, iPhone 13, Pixel 7):
// no horizontal scroll, tab labels not clipped, tab targets at least 44 px (design language §4).
const WIDTHS = [375, 390, 412]

for (const [mode, baseURL] of [
  ['demo', DEMO_URL],
  ['owner', LIVE_URL],
] as const) {
  test.describe(`${mode} build`, () => {
    test.use({ baseURL })

    test.beforeEach(async ({ page }) => {
      if (mode !== 'owner') return
      await signInAs(page)
      await mockApi(page, {
        today: { json: inSeason.today },
        matchup: { json: inSeason.matchup },
        waivers: { json: inSeason.waivers },
        players: { json: draftPlayers() },
      })
    })

    for (const width of WIDTHS) {
      test(`no horizontal scroll on any route at ${width} px`, async ({ page }) => {
        await page.setViewportSize({ width, height: 800 })
        for (const route of ROUTES) {
          await page.goto(route)
          await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
          const o = await overflowX(page)
          expect(o.scrollWidth, `${route} at ${width} px`).toBeLessThanOrEqual(o.innerWidth)
        }
        // The player sheet and an expanded action fit too.
        await page.goto('/players')
        await page.getByRole('button', { name: /Victor Wembanyama/ }).click()
        await expect(page.getByRole('dialog')).toBeVisible()
        const box = await page.getByRole('dialog').boundingBox()
        expect((box?.x ?? -1) >= 0 && (box?.x ?? 0) + (box?.width ?? 0) <= width + 0.5).toBe(true)
        await page.goto('/today')
        await page.getByRole('button', { name: /Start Keegan Murray/ }).click()
        const o = await overflowX(page)
        expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
      })
    }

    test('the tab bar: labels not clipped, targets at least 44 px', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 800 })
      await page.goto('/today')
      const nav = page.getByRole('navigation', { name: 'Main' })
      for (const tab of TABS) {
        const link = nav.getByRole('link', { name: tab })
        await expect(link).toBeInViewport({ ratio: 1 })
        const box = await link.boundingBox()
        expect(box?.height ?? 0, `${tab} height`).toBeGreaterThanOrEqual(44)
        expect(box?.width ?? 0, `${tab} width`).toBeGreaterThanOrEqual(44)
        const clipped = await link.evaluate(
          (el) => el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight,
        )
        expect(clipped, `${tab} label clipped`).toBe(false)
        await expect(link).toHaveText(tab)
      }
    })
  })
}
