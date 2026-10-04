import { DEMO_URL } from './support/urls'
import { ROUTES, expect, overflowX, test } from './support/test'

// Persona: a laptop at 1280 × 800 (and a wide monitor at 1600). Design language §9: a sidebar, wide content.
test.use({ baseURL: DEMO_URL })

test.beforeEach(async ({ isMobile }) => {
  test.skip(!!isMobile, 'the desktop persona runs on the desktop project')
})

test('every route: a sidebar on the left, content filling the rest, no tab bar', async ({
  page,
}) => {
  for (const route of ROUTES) {
    await page.goto(route)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    const nav = page.getByRole('navigation', { name: 'Main' })
    await expect(nav).toHaveAttribute('data-variant', 'sidebar')
    const main = await page.locator('main').boundingBox()
    const side = await nav.boundingBox()
    if (!main || !side) throw new Error('no main or nav')
    expect(side.x).toBeLessThan(main.x)
    expect(main.x + main.width, `${route} fills to the edge`).toBeGreaterThanOrEqual(1270)
    const o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
  }
})

test('the content is capped at 1200 px on a wide monitor', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 900 })
  await page.goto('/players')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  const col = await page.locator('main > div').boundingBox()
  if (!col) throw new Error('no column')
  expect(col.width).toBeLessThanOrEqual(1200)
  expect(col.width).toBeGreaterThan(1000)
})

test('the table answers the pointer, and the detail opens beside it (WEB-024)', async ({
  page,
}, info) => {
  await page.goto('/players')
  const table = page.getByRole('table', { name: 'Players' })
  const row = table.locator('tbody tr').filter({ hasText: 'Victor Wembanyama' })
  await row.hover()
  await expect(row).toHaveCSS('cursor', 'pointer')
  // The hover state, kept in the report for a human look (design language §8).
  await info.attach('players-row-hover', {
    body: await page.screenshot(),
    contentType: 'image/png',
  })
  await row.click()
  const panel = page.getByRole('complementary', { name: 'Victor Wembanyama' })
  await expect(panel).toBeVisible()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  const t = await table.boundingBox()
  const p = await panel.boundingBox()
  if (!t || !p) throw new Error('no table or panel')
  expect(p.x).toBeGreaterThanOrEqual(t.x + t.width) // beside, not over, the table
  await expect(row).toHaveAttribute('data-selected', 'true')
  const o = await overflowX(page)
  expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
})

test('between 840 and 1199 px the table stays and the detail is a centred sheet', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1000, height: 800 })
  await page.goto('/players')
  await page.getByRole('button', { name: 'Victor Wembanyama', exact: true }).click()
  const sheet = await page.getByRole('dialog').boundingBox()
  if (!sheet) throw new Error('no sheet')
  expect(sheet.y).toBeGreaterThan(0) // centred, not pinned to the bottom edge as on phones
  expect(sheet.y + sheet.height).toBeLessThan(800)
  const o = await overflowX(page)
  expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
})
