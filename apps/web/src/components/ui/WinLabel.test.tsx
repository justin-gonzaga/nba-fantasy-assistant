import { render, screen } from '@testing-library/react'
import { WinLabel, winState } from './WinLabel'

describe('winState', () => {
  it.each([
    [0.6, 'Winning'],
    [0.59, 'Toss-up'],
    [0.41, 'Toss-up'],
    [0.4, 'Losing'],
  ])('%s -> %s', (p, word) => {
    expect(winState(p).word).toBe(word)
  })
})

describe('WinLabel', () => {
  it('never relies on colour alone: it always has words', () => {
    render(<WinLabel p={0.28} showPct />)
    expect(screen.getByText(/Losing 28%/)).toBeInTheDocument()
  })
})
