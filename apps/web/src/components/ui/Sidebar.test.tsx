import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { Sidebar } from './Sidebar'

describe('Sidebar (WEB-029)', () => {
  it('lists the five destinations and the practice tools; unchanged by the phone Practice tab', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )
    const main = within(screen.getByRole('navigation', { name: 'Main' }))
    expect(main.getAllByRole('link').map((a) => a.textContent)).toEqual([
      'Today',
      'Matchup',
      'Waivers',
      'Players',
      'Ask',
    ])
    const tools = within(screen.getByRole('navigation', { name: 'Tools' }))
    expect(tools.getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual([
      '/draft',
      '/replay',
      '/sims',
    ])
  })
})
