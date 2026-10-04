import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { inSeason } from './fixtures/brief'
import { draftPlayers } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import { expect, mockApi, overflowX, signInAs, test } from './support/test'

// Persona: the owner on a phone the week before the auction, one thumb, no URL bar. "How do I get to the
// practice room?" (WEB-029)

const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']
const SIX = ['Today', 'Matchup', 'Waivers', 'Players', 'Ask', 'Practice']

test.use({ baseURL: LIVE_URL })

test.beforeEach(async ({ page, isMobile }) => {
  test.skip(!isMobile, 'the tab bar is the phone layout; desktop has the sidebar')
  await signInAs(page)
  await mockApi(page, {
    today: { json: inSeason.today },
    matchup: { json: inSeason.matchup },
    waivers: { json: inSeason.waivers },
    players: () => ({ json: draftPlayers('all') }),
    'me/sims': { json: [] },
  })
})

async function fits(page: Page, label: string) {
  const o = await overflowX(page)
  expect(o.scrollWidth, label).toBeLessThanOrEqual(o.innerWidth)
}

for (const [width, height] of [
  [320, 568],
  [390, 844],
] as const) {
  test(`six tabs fit at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height })
    await page.goto('/today')
    const bar = page.getByRole('navigation', { name: 'Main' })
    await expect(bar.getByRole('link')).toHaveCount(6)
    for (const name of SIX) {
      const link = bar.getByRole('link', { name, exact: true })
      const box = await link.boundingBox()
      if (!box) throw new Error(`no box for ${name}`)
      expect(box.width, `${name} width`).toBeGreaterThanOrEqual(44)
      expect(box.height, `${name} height`).toBeGreaterThanOrEqual(44)
      expect(box.x + box.width, `${name} inside the viewport`).toBeLessThanOrEqual(width)
      const clipped = await link.evaluate((el) => el.scrollWidth > el.clientWidth)
      expect(clipped, `${name} label clipped`).toBe(false)
    }
    await fits(page, 'today')
  })
}

test('tap to the practice room, Season replay and Past sims', async ({ page }) => {
  test.slow()
  await page.goto('/today')
  const bar = page.getByRole('navigation', { name: 'Main' })
  await expect(page.getByRole('heading', { level: 1, name: '5–3–1' })).toBeVisible()

  await bar.getByRole('link', { name: 'Practice', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Practice' })).toBeVisible()
  await expect(page.getByText(/^Resume/)).toHaveCount(0)
  await fits(page, 'hub')
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze()
  expect(violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')).toEqual([])

  await page.getByRole('link', { name: /Draft practice/ }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Draft practice' })).toBeVisible()
  await expect(bar.getByRole('link', { name: 'Practice' })).toHaveAttribute('aria-current', 'page')
  await fits(page, 'setup')
  await page.getByRole('radio', { name: /Real timers/ }).check()
  await page.getByRole('button', { name: 'Start practice draft' }).click()
  await expect(page.getByTestId('clock-ring').first()).toBeVisible()
  await fits(page, 'room')
  const vp = page.viewportSize()
  const sim = page.getByRole('button', { name: 'Sim the rest' })
  const box = await sim.boundingBox()
  if (!vp || !box) throw new Error('no layout')
  expect(box.x + box.width).toBeLessThanOrEqual(vp.width)

  await bar.getByRole('link', { name: 'Practice', exact: true }).click()
  await expect(page.getByRole('link', { name: /Resume your draft/ })).toBeVisible()
  await page.getByRole('link', { name: /Season replay/ }).click()
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(bar.getByRole('link', { name: 'Practice' })).toHaveAttribute('aria-current', 'page')
  await fits(page, 'replay')

  await bar.getByRole('link', { name: 'Practice', exact: true }).click()
  await page.getByRole('link', { name: /Past sims/ }).click()
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(bar.getByRole('link', { name: 'Practice' })).toHaveAttribute('aria-current', 'page')
  await fits(page, 'sims')
})

test('practice pages fit the phone, report included', async ({ page }) => {
  test.slow()
  await page.goto('/draft')
  await page.getByRole('radio', { name: /Untimed/ }).check()
  await page.getByRole('button', { name: 'Start practice draft' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Draft practice' })).toBeVisible()
  await page.getByRole('button', { name: 'Sim the rest' }).click()
  await expect(page.getByText('Practice draft complete')).toBeVisible()
  await fits(page, 'report')
  const vp = page.viewportSize()
  if (!vp) throw new Error('no viewport')
  for (const b of await page.getByRole('button').all()) {
    if (!(await b.isVisible())) continue
    const box = await b.boundingBox()
    if (box) expect(box.x + box.width, await b.innerText()).toBeLessThanOrEqual(vp.width)
  }
})
