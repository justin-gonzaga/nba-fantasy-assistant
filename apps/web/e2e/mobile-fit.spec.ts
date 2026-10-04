import { DEMO_URL } from './support/urls'
import { expect, test } from './support/test'
import type { Page } from '@playwright/test'

// Persona: a phone owner on a small or mid screen. Nothing may be wider than the viewport, a control
// must not trigger iOS focus zoom, and the tab bar must not move when tabs are tapped.
const ROUTES = [
  '/today',
  '/matchup',
  '/waivers',
  '/players',
  '/ask',
  '/practice',
  '/draft',
  '/replay',
  '/sims',
]
const WIDTHS = [320, 360, 390]

/** Elements sticking out of the viewport that no scrolling container of their own explains. */
async function strays(page: Page) {
  return page.evaluate(() => {
    const limit = window.innerWidth + 0.5
    const scrolls = (el: Element) => {
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        const o = getComputedStyle(p).overflowX
        if (o === 'auto' || o === 'scroll' || o === 'hidden' || o === 'clip') return true
      }
      return false
    }
    const out: string[] = []
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect()
      if (r.width > 0 && (r.right > limit || r.left < -0.5) && !scrolls(el))
        out.push(
          `${el.tagName.toLowerCase()}.${String(el.className).slice(0, 50)} ${Math.round(r.left)}..${Math.round(r.right)}`,
        )
    }
    return out.slice(0, 5)
  })
}

test.describe('mobile fit', () => {
  test.use({ baseURL: DEMO_URL })
  test.skip(({ isMobile }) => !isMobile, 'phone projects only')

  for (const width of WIDTHS) {
    test(`nothing is wider than the screen at ${width} px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 740 })
      for (const route of ROUTES) {
        await page.goto(route)
        await expect(page.getByRole('main')).toBeVisible()
        await page.waitForLoadState('networkidle')
        expect(await strays(page), `${route} at ${width} px`).toEqual([])
        const o = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        )
        expect(o, `${route} scroll width at ${width} px`).toBeLessThanOrEqual(0)
      }
    })
  }

  test('controls are at least 16 px so iOS does not zoom the page on focus', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 740 })
    for (const route of ROUTES) {
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      const small = await page.evaluate(() =>
        [...document.querySelectorAll<HTMLElement>('input, select, textarea')]
          .filter(
            (e) => !['checkbox', 'radio', 'range', 'hidden'].includes((e as HTMLInputElement).type),
          )
          .map((e) => ({ tag: e.tagName, size: parseFloat(getComputedStyle(e).fontSize) }))
          .filter((c) => c.size < 16),
      )
      expect(small, route).toEqual([])
    }
  })

  test('the tab bar does not move or resize when tabs are tapped', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 740 })
    await page.goto('/today')
    const nav = page.getByRole('navigation', { name: 'Main' })
    const measure = () =>
      nav.evaluate((el) => {
        const r = el.getBoundingClientRect()
        const links = [...el.querySelectorAll('a')].map((a) =>
          Math.round(a.getBoundingClientRect().width * 10),
        )
        return { top: Math.round(r.top), height: Math.round(r.height), links }
      })
    const first = await measure()
    for (const tab of ['Matchup', 'Waivers', 'Players', 'Ask', 'Practice', 'Today']) {
      await nav.getByRole('link', { name: tab }).click()
      await expect(nav.getByRole('link', { name: tab })).toHaveAttribute('aria-current', 'page')
      expect(await measure(), tab).toEqual(first)
    }
  })
})
