// DRAFT-020 AC8 visual QA: the clock in its calm, warn and urgent states, with a fake page clock.
// Not part of the normal suite: run with `just web-screens` (SCREENS=1).
import { test } from '@playwright/test'
import { draftPlayers } from './fixtures/players'
import { expect, mockApi, problem, signInAs } from './support/test'
import { LIVE_URL } from './support/urls'

const OUT = process.env.SCREENS_DIR ?? 'screens'

test.skip(!process.env.SCREENS, 'screenshots run only on request (SCREENS=1)')
test.use({ baseURL: LIVE_URL, contextOptions: { reducedMotion: 'no-preference' } })

test('draft clock: calm, warn, urgent', async ({ page }, info) => {
  await page.clock.install()
  await signInAs(page)
  await mockApi(page, {
    today: problem(404, 'no-brief'),
    players: () => ({ json: draftPlayers('all') }),
  })
  await page.goto('/draft')
  await page.getByRole('radio', { name: /Real timers/ }).check()
  await page.getByRole('button', { name: 'Start practice draft' }).click()
  const ring = page.getByTestId('clock-ring')
  await expect(ring).toBeVisible()

  const leftNow = async () => Number(await ring.innerText())
  for (const [state, target] of [
    ['calm', 12],
    ['warn', 8],
    ['urgent', 3],
  ] as const) {
    const left = await leftNow()
    if (left > target) await page.clock.runFor((left - target) * 1000 - 100)
    await expect(ring).toHaveAttribute('data-phase', state)
    await page.screenshot({
      path: `${OUT}/${info.project.name}-draft-clock-${state}.png`,
      fullPage: false,
    })
  }
})
