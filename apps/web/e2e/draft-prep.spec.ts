import { PLAYER_COUNT, draftPlayers, healthiestFirst } from './fixtures/players'
import { LIVE_URL } from './support/urls'
import {
  expect,
  filterChip,
  mockApi,
  playerDetail,
  playerRows,
  signInAs,
  test,
} from './support/test'

// Persona: the owner preparing for the draft. "Show me injury-prone players and open one."
test.use({ baseURL: LIVE_URL })

const all = draftPlayers().players
const injuryProne = all.filter((p) => p.badges?.some((b) => b.code === 'injury_prone'))

test.beforeEach(async ({ page }) => {
  await signInAs(page)
  await mockApi(page, { players: { json: draftPlayers() } })
})

test('the badge filter keeps only injury-prone players, and the URL keeps the filter', async ({
  page,
}) => {
  await page.goto('/players')
  await expect(page.getByText(`${PLAYER_COUNT} players`)).toBeVisible()
  const chip = await filterChip(page, 'badge', /^Injury prone/)
  await chip.click()
  await expect(chip).toHaveAttribute('aria-pressed', 'true')
  await expect(page).toHaveURL(/badge=injury_prone/)
  await expect(page.getByText(`${injuryProne.length} of ${PLAYER_COUNT} players`)).toBeVisible()
  const rows = playerRows(page)
  await expect(rows).toHaveCount(injuryProne.length)
  for (const row of await rows.all()) await expect(row.getByText('Injury prone')).toBeVisible()

  await page.reload()
  await expect(rows).toHaveCount(injuryProne.length)
})

test('the detail sheet lists every badge with its why line and the healthy rank', async ({
  page,
}) => {
  const chet = all.find((p) => p.name === 'Chet Holmgren')
  await page.goto('/players?badge=injury_prone')
  await page.getByRole('button', { name: /Chet Holmgren/ }).click()
  const sheet = playerDetail(page, 'Chet Holmgren')
  await expect(sheet.getByRole('heading', { name: 'Badges' })).toBeVisible()
  const badges = sheet.getByRole('list', { name: 'Badges' }).getByRole('listitem')
  await expect(badges).toHaveCount(2)
  await expect(badges.nth(0)).toContainText('Injury prone')
  await expect(badges.nth(0)).toContainText(
    'Played 82, 32 and 45 of 82 games in the last three seasons',
  )
  await expect(badges.nth(1)).toContainText('Bounce-back')
  await expect(badges.nth(1)).toContainText('Bounce-back chance 41 % (top 20 %)')
  await expect(sheet).toContainText(
    `Ranked #7 after expected missed games (70 of 82); #${chet?.healthyRank} if he plays 72.`,
  )
})

test('the healthy-rank sort puts the best player at 72 games first', async ({ page }) => {
  await page.goto('/players')
  const first = playerRows(page).first()
  await expect(first).toContainText('Nikola Jokić')
  await page.getByRole('combobox', { name: 'Sort' }).selectOption({ label: 'Healthy rank' })
  await expect(page).toHaveURL(/sort=healthy/)
  await expect(first).toContainText(healthiestFirst.name)
  expect(healthiestFirst.name).not.toBe('Nikola Jokić') // the sort really changes the order
})
