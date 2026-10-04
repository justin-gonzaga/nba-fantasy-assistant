// WEB-023 visual QA: full-page screenshots of every route (demo build) for design review.
// Not part of the normal suite: run with `just web-screens` (see justfile).
import { test } from '@playwright/test'
import { draftPlayers } from './fixtures/players'
import { ROUTES, mockApi, signInAs } from './support/test'
import { LIVE_URL } from './support/urls'

const OUT = process.env.SCREENS_DIR ?? 'screens'

test.skip(!process.env.SCREENS, 'screenshots run only on request (SCREENS=1)')

for (const route of ROUTES) {
  test(`screen ${route}`, async ({ page }, info) => {
    await page.goto(route)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(400) // let entry animations settle
    const name = `${info.project.name}${route.replace(/\//g, '-')}`
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
  })
}

test('screen player detail', async ({ page }, info) => {
  await page.goto('/players')
  await page
    .getByRole('button', { name: /Nikola Joki/ })
    .first()
    .click()
  await page.waitForTimeout(500)
  await page.screenshot({ path: `${OUT}/${info.project.name}-player-detail.png`, fullPage: false })
})

test.describe('signed out (owner build)', () => {
  test.use({ baseURL: LIVE_URL })

  test('screen landing', async ({ page }, info) => {
    await page.goto('/today')
    await page.getByRole('button', { name: 'Sign in with Google' }).waitFor()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-landing.png`, fullPage: true })
  })
})

test('screen practice hub', async ({ page }, info) => {
  await page.goto('/practice')
  await page.waitForTimeout(400)
  await page.screenshot({ path: `${OUT}/${info.project.name}-practice.png`, fullPage: true })
  await page.setViewportSize({ width: 320, height: 568 })
  await page.screenshot({ path: `${OUT}/${info.project.name}-practice-320.png`, fullPage: true })
})

test.describe('draft practice (owner build)', () => {
  test.use({ baseURL: LIVE_URL })

  test('screen draft room', async ({ page }, info) => {
    await signInAs(page)
    await mockApi(page, { players: () => ({ json: draftPlayers('all') }) })
    await page.goto('/draft')
    await page.screenshot({ path: `${OUT}/${info.project.name}-draft-setup.png`, fullPage: true })
    await page.getByRole('button', { name: 'Start practice draft' }).click()
    await page.getByText('Current bid').or(page.getByText('Your nomination')).first().waitFor()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-draft-room.png`, fullPage: true })
    await page.getByRole('button', { name: 'Sim the rest' }).click()
    await page.getByText('Your report').waitFor()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-draft-report.png`, fullPage: true })
  })
})

test.describe('season replay (owner build)', () => {
  test.use({ baseURL: LIVE_URL })

  test('screen season replay', async ({ page }, info) => {
    const { draftedLeague, replayWithGames } =
      await import('../src/features/replay/fixtures/replayWithGames')
    await signInAs(page)
    await page.addInitScript(
      (l) => window.localStorage.setItem('replay-league', l),
      JSON.stringify(draftedLeague()),
    )
    await mockApi(page, {
      'replay/seasons': { json: { seasons: ['2024-25'] } },
      'replay/2024-25': { json: replayWithGames('2024-25') },
    })
    await page.goto('/replay')
    await page.getByRole('table', { name: 'Your team’s week' }).waitFor()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-replay-week.png`, fullPage: true })
    await page.getByRole('button', { name: 'Play the week' }).click()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-replay-result.png`, fullPage: true })
  })
})

test.describe('past sims (owner build)', () => {
  test.use({ baseURL: LIVE_URL })

  test('screen past sims', async ({ page }, info) => {
    await signInAs(page)
    const run = (i: number, title: string, surplus: number, wins: number) => ({
      id: `run-${i}`,
      kind: 'practice',
      season: '2026-27',
      title,
      summary: { surplus, categoryWins: wins, counted: 9, at: `2026-10-0${i}` },
      pinned: i === 2,
      hasDetail: true,
      createdAt: `2026-10-0${i}T09:00:00Z`,
      updatedAt: `2026-10-0${i}T09:00:00Z`,
      version: 1,
    })
    await mockApi(page, {
      'me/sims': {
        json: [
          run(5, 'All categories', 6, 5.1),
          run(4, 'Punt FT%', 11, 5.6),
          run(3, 'All categories', 3, 4.8),
          run(2, 'Punt FT%', 9, 5.2),
          run(1, 'All categories', -4, 4.1),
        ],
      },
    })
    await page.goto('/sims')
    await page.getByRole('list', { name: 'Your practice drafts' }).waitFor()
    await page.waitForTimeout(400)
    await page.screenshot({ path: `${OUT}/${info.project.name}-past-sims.png`, fullPage: true })
  })
})
