import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StateCard } from './StateCard'

describe('StateCard (WEB-016 AC1)', () => {
  it.each([
    ['neutral', 'status'],
    ['warn', 'status'],
    ['error', 'alert'],
  ] as const)('a %s card is announced as %s', (tone, role) => {
    render(
      <StateCard tone={tone} title="Title">
        Body
      </StateCard>,
    )
    const region = screen.getByRole(role)
    expect(region).toHaveTextContent('TitleBody')
    expect(region.querySelector('svg[aria-hidden="true"]')).not.toBeNull() // an icon, not colour alone
  })

  it('renders its action outside the live region', () => {
    render(<StateCard title="T" action={<button type="button">Retry</button>} />)
    expect(screen.getByRole('status')).not.toContainElement(
      screen.getByRole('button', { name: 'Retry' }),
    )
  })
})
