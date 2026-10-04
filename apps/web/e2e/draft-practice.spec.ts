import { draftPlayers } from './fixtures/players'
import { DEMO_URL, LIVE_URL } from './support/urls'
import { expect, mockApi, overflowX, problem, signInAs, test } from './support/test'

// Persona: the owner a week before the auction. "Let me practise against a room." (DRAFT-014)

test.describe('signed in, with this season’s values', () => {
  test.use({ baseURL: LIVE_URL })

  test.beforeEach(async ({ page }) => {
    await signInAs(page)
    await mockApi(page, {
      today: problem(404, 'no-brief'),
      players: () => ({ json: draftPlayers('all') }),
    })
  })

  test('plays a practice auction: bid, pass, then sim the rest to a full team', async ({
    page,
  }) => {
    // A long scenario (start, five lots, sim to the end): emulated WebKit on CI runs it in 20-30 s.
    test.slow()
    await page.goto('/draft')
    await page.getByRole('radio', { name: /Untimed/ }).check()
    await page.getByRole('button', { name: 'Start practice draft' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Draft practice' })).toBeVisible()
    let o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)

    // DRAFT-016 AC4: on a lot, the verdict and the bid button are visible without scrolling
    const verdict = page.getByTestId('verdict')
    if (await verdict.isVisible()) {
      const vp = page.viewportSize()
      const box = await page
        .getByRole('button', { name: /^Bid \$\d+$/ })
        .first()
        .boundingBox()
      const vbox = await verdict.boundingBox()
      if (!vp || !box || !vbox) throw new Error('no layout')
      expect(vbox.y + vbox.height).toBeLessThanOrEqual(vp.height)
      expect(box.y + box.height).toBeLessThanOrEqual(vp.height)
    }

    // Five lots by hand: bid when it's a lot (pass if outbid), nominate the top target when it's my turn.
    for (let i = 0; i < 5; i++) {
      const pass = page.getByRole('button', { name: 'Pass' })
      if (await pass.isVisible()) {
        await pass.click()
      } else {
        await page.getByRole('list', { name: 'Your targets' }).getByRole('button').first().click()
      }
    }
    await expect(
      page.getByRole('list', { name: 'Recent sales' }).getByRole('listitem'),
    ).not.toHaveCount(0)

    await page.getByRole('button', { name: 'Sim the rest' }).click()
    await expect(page.getByText('Practice draft complete')).toBeVisible()
    await expect(
      page.getByRole('list', { name: 'Category ranks' }).getByRole('listitem'),
    ).toHaveCount(9)
    await expect(
      page.getByRole('table', { name: 'Your drafted team' }).getByRole('row'),
    ).toHaveCount(15)
    o = await overflowX(page)
    expect(o.scrollWidth).toBeLessThanOrEqual(o.innerWidth)
  })
})

test.describe('demo build', () => {
  test.use({ baseURL: DEMO_URL })

  test('the 10-player sample explains why practice needs the full pool', async ({ page }) => {
    await page.goto('/draft')
    await expect(page.getByText('Practice needs the full player pool')).toBeVisible()
  })
})
