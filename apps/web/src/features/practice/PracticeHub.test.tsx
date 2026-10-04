import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { SAVE_KEY } from '../draft/practice'
import { saveLeague } from '../replay/league'
import { PracticeHub } from './PracticeHub'

const show = () =>
  render(
    <MemoryRouter>
      <PracticeHub />
    </MemoryRouter>,
  )

beforeEach(() => localStorage.clear())

describe('PracticeHub (WEB-029)', () => {
  it('links every practice tool that has a route', () => {
    show()
    expect(screen.getByRole('heading', { level: 1, name: 'Practice' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Draft practice/ })).toHaveAttribute('href', '/draft')
    expect(screen.getByRole('link', { name: /Season replay/ })).toHaveAttribute('href', '/replay')
    expect(screen.getByRole('link', { name: /Past sims/ })).toHaveAttribute('href', '/sims')
  })

  it('resume appears only with a saved run', () => {
    const { unmount } = show()
    expect(screen.queryByText(/Resume/)).not.toBeInTheDocument()
    unmount()

    localStorage.setItem(SAVE_KEY, JSON.stringify({ settings: {}, sales: [], turn: 3 }))
    saveLeague({
      version: 1,
      season: '2024-25',
      me: 'T1',
      rosters: { T1: [1] },
      savedAt: '2026-10-04T00:00:00Z',
      results: {},
    })
    show()
    expect(screen.getByRole('link', { name: /Resume your draft/ })).toHaveAttribute(
      'href',
      '/draft',
    )
    expect(screen.getByRole('link', { name: /Resume your season/ })).toHaveAttribute(
      'href',
      '/replay',
    )
  })

  it('ignores a corrupt save', () => {
    localStorage.setItem(SAVE_KEY, '{nope')
    show()
    expect(screen.queryByText(/Resume/)).not.toBeInTheDocument()
  })
})
