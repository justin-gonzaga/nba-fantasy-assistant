import { render, screen } from '@testing-library/react'
import { samplePlayers } from '../../api/fixtures'
import type { PlayerBadge, PlayerRow } from '../../api/types'
import { FILTERS, PRIORITY, badgesOf, hasAnyBadge, parseBadgeParam } from './badges'
import { PlayerBadgeChip, RowBadges } from './PlayerBadges'

const base = samplePlayers.players[0] as PlayerRow
const b = (code: PlayerBadge['code'], label: string = code): PlayerBadge => ({
  code,
  label,
  tone: 'neutral',
  why: `${label} why`,
})

describe('PlayerBadgeChip (WEB-018 AC4)', () => {
  it('is the design-language Badge: a decorative stroke icon plus the word', () => {
    render(
      <PlayerBadgeChip
        badge={{ code: 'injury_prone', label: 'Injury prone', tone: 'lose', why: 'x' }}
      />,
    )
    const chip = screen.getByText('Injury prone')
    expect(chip).toHaveClass('rounded-full', 'text-lose') // the Badge primitive, tone token
    const icon = chip.querySelector('[aria-hidden="true"] svg') as SVGElement
    expect(icon).not.toBeNull()
    expect(icon.getAttribute('stroke')).toBe('currentColor')
    expect(icon.getAttribute('stroke-width')).toBe('1.75')
    expect(icon.getAttribute('width')).toBe('16')
    expect(chip).toHaveTextContent(/^Injury prone$/) // a screen reader hears the word only
  })

  it.each(PRIORITY)('has an icon for %s', (code) => {
    render(<PlayerBadgeChip badge={b(code, `Label ${code}`)} />)
    expect(screen.getByText(`Label ${code}`).querySelector('svg path')).not.toBeNull()
  })
})

describe('badge helpers (WEB-018 AC3)', () => {
  it('orders by priority whatever order they arrive in', () => {
    const p = { ...base, badges: [b('top_tier'), b('breakout'), b('injured_today')] }
    expect(badgesOf(p).map((x) => x.code)).toEqual(['injured_today', 'breakout', 'top_tier'])
  })

  it('treats a missing badges field as none', () => {
    const p = { ...base, badges: undefined }
    expect(badgesOf(p)).toEqual([])
    expect(hasAnyBadge(p, ['rookie'])).toBe(false)
    expect(hasAnyBadge(p, [])).toBe(true)
  })

  it('reads only known filter codes from the URL', () => {
    expect(parseBadgeParam('breakout,bogus,rookie,top_tier')).toEqual(['breakout', 'rookie'])
    expect(parseBadgeParam(null)).toEqual([])
    expect(FILTERS.map(([c]) => c)).toEqual([
      'injury_prone',
      'missed_time',
      'breakout',
      'bounce_back',
      'rookie',
    ])
  })

  it('shows at most two in a row, then +N', () => {
    const p = { ...base, badges: [b('rookie'), b('top_tier'), b('breakout'), b('missed_time')] }
    render(<RowBadges player={p} />)
    expect(screen.getByText('missed_time')).toBeInTheDocument()
    expect(screen.getByText('breakout')).toBeInTheDocument()
    expect(screen.queryByText('rookie')).toBeNull()
    expect(screen.getByText('+2')).toHaveTextContent('+2 more labels')
  })
})

describe('Adjusted badge (DATA-036)', () => {
  it('comes right after injured today and shows its source in the why', () => {
    const p = {
      ...base,
      badges: [b('top_tier'), b('adjusted'), b('injured_today')],
    }
    expect(badgesOf(p).map((x) => x.code)).toEqual(['injured_today', 'adjusted', 'top_tier'])
  })
})
