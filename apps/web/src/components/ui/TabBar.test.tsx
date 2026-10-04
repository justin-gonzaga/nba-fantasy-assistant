import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { TabBar } from './TabBar'

const at = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <TabBar />
    </MemoryRouter>,
  )

describe('TabBar (WEB-029)', () => {
  it('has six tabs, Practice last, in one Main landmark', () => {
    at('/today')
    const nav = screen.getByRole('navigation', { name: 'Main' })
    const links = nav.querySelectorAll('a')
    expect(links).toHaveLength(6)
    expect(links[5]).toHaveTextContent('Practice')
    expect(links[5]).toHaveAttribute('href', '/practice')
  })

  it.each(['/practice', '/draft', '/replay', '/sims', '/sims/run:1'])(
    'Practice is the active tab on %s',
    (path) => {
      at(path)
      const active = screen
        .getAllByRole('link')
        .filter((a) => a.getAttribute('aria-current') === 'page')
      expect(active.map((a) => a.textContent)).toEqual(['Practice'])
    },
  )

  it('Practice is not active on the other tabs', () => {
    at('/players')
    expect(screen.getByRole('link', { name: 'Practice' })).not.toHaveAttribute('aria-current')
    expect(screen.getByRole('link', { name: 'Players' })).toHaveAttribute('aria-current', 'page')
  })
})
