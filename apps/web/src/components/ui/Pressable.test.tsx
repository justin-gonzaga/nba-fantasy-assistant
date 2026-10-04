import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'
import { Chip } from './Chip'
import { Pressable } from './Pressable'
import { Surface } from './Surface'

const INTERACTIVE = ['cursor-pointer', 'focus-visible:outline-2', 'focus-visible:outline-accent']

describe('Pressable (AC3)', () => {
  it('is a button with pointer cursor, lift, light, press and a focus-visible ring', () => {
    render(<Pressable>Row</Pressable>)
    const b = screen.getByRole('button', { name: 'Row' })
    expect(b).toHaveAttribute('type', 'button')
    expect(b).toHaveClass(...INTERACTIVE, 'lift', 'light', 'press')
  })

  it('moves the light with a mouse pointer', () => {
    render(<Pressable>Row</Pressable>)
    const b = screen.getByRole('button')
    fireEvent.pointerMove(b, { pointerType: 'mouse', clientX: 30, clientY: 12 })
    expect(b.style.getPropertyValue('--x')).toBe('30px')
    expect(b.style.getPropertyValue('--y')).toBe('12px')
    fireEvent.pointerMove(b, { pointerType: 'mouse', clientX: 41, clientY: 5 })
    expect(b.style.getPropertyValue('--x')).toBe('41px')
  })

  it('ignores touch and pen pointers (no hover on touch)', () => {
    render(<Pressable>Row</Pressable>)
    const b = screen.getByRole('button')
    fireEvent.pointerMove(b, { pointerType: 'touch', clientX: 30, clientY: 12 })
    fireEvent.pointerMove(b, { pointerType: 'pen', clientX: 30, clientY: 12 })
    expect(b.style.getPropertyValue('--x')).toBe('')
  })

  it('still calls the caller’s handlers', async () => {
    const onClick = vi.fn()
    const onPointerMove = vi.fn()
    render(
      <Pressable onClick={onClick} onPointerMove={onPointerMove}>
        Row
      </Pressable>,
    )
    const b = screen.getByRole('button')
    fireEvent.pointerMove(b, { pointerType: 'mouse', clientX: 1, clientY: 1 })
    await userEvent.click(b)
    expect(onPointerMove).toHaveBeenCalled()
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('the bare variant keeps cursor, press and focus but no lift', () => {
    render(<Pressable variant="bare">Row</Pressable>)
    const b = screen.getByRole('button')
    expect(b).toHaveClass(...INTERACTIVE, 'press')
    expect(b).not.toHaveClass('lift')
  })

  it('shows not-allowed when disabled', () => {
    render(<Pressable disabled>Row</Pressable>)
    expect(screen.getByRole('button')).toHaveClass('disabled:cursor-not-allowed')
  })
})

describe('Button and Chip (AC3)', () => {
  it.each(['primary', 'secondary'] as const)('%s button is interactive and presses', (v) => {
    render(<Button variant={v}>Go</Button>)
    expect(screen.getByRole('button', { name: 'Go' })).toHaveClass(
      ...INTERACTIVE,
      'press-strong',
      'min-h-11',
    )
  })

  it('a chip reports its pressed state and presses', () => {
    render(<Chip pressed>BLK</Chip>)
    const c = screen.getByRole('button', { name: 'BLK' })
    expect(c).toHaveAttribute('aria-pressed', 'true')
    expect(c).toHaveClass(...INTERACTIVE, 'press-strong')
  })
})

describe('Surface (AC3)', () => {
  it('is a resting card by default: no light, no lift', () => {
    render(<Surface>Card</Surface>)
    const s = screen.getByText('Card')
    expect(s).toHaveClass('surface', 'rounded-card')
    expect(s).not.toHaveClass('light')
    fireEvent.pointerMove(s, { pointerType: 'mouse', clientX: 3, clientY: 4 })
    expect(s.style.getPropertyValue('--x')).toBe('')
  })

  it('interactive surfaces lift and follow a mouse with the light', () => {
    render(
      <Surface as="li" interactive>
        Card
      </Surface>,
    )
    const s = screen.getByRole('listitem')
    expect(s).toHaveClass('lift', 'light')
    fireEvent.pointerMove(s, { pointerType: 'mouse', clientX: 3, clientY: 4 })
    expect(s.style.getPropertyValue('--y')).toBe('4px')
    fireEvent.pointerMove(s, { pointerType: 'touch', clientX: 9, clientY: 9 })
    expect(s.style.getPropertyValue('--y')).toBe('4px')
  })
})
