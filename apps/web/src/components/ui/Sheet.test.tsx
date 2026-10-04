import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { Sheet } from './Sheet'

function Harness({ onClose = () => {} }: { onClose?: () => void }) {
  const [open, setOpen] = useState(true)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Open
      </button>
      {open && (
        <Sheet
          labelledBy="t"
          onClose={() => {
            onClose()
            setOpen(false)
          }}
        >
          <h2 id="t">Title</h2>
          <button type="button">First</button>
          <button type="button">Last</button>
        </Sheet>
      )}
    </>
  )
}

const grabber = () => screen.getByTestId('sheet-grabber')

describe('Sheet (AC3)', () => {
  it('is a labelled modal dialog that animates in from its layer', () => {
    render(<Harness />)
    const d = screen.getByRole('dialog', { name: 'Title' })
    expect(d).toHaveAttribute('aria-modal', 'true')
    expect(d).toHaveClass('sheet-panel', 'material')
    expect(d).toHaveAttribute('data-state', 'open')
  })

  it('focuses the first control and traps Tab inside', async () => {
    render(<Harness />)
    const first = screen.getByRole('button', { name: 'First' })
    const last = screen.getByRole('button', { name: 'Last' })
    expect(first).toHaveFocus()
    await userEvent.tab()
    expect(last).toHaveFocus()
    await userEvent.tab()
    expect(first).toHaveFocus()
    await userEvent.tab({ shift: true })
    expect(last).toHaveFocus()
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    render(<Harness onClose={onClose} />)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledOnce()
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('returns focus to the control that opened it', async () => {
    function Closed() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>
            Open
          </button>
          {open && (
            <Sheet labelledBy="t2" onClose={() => setOpen(false)}>
              <h2 id="t2">Title</h2>
              <button type="button">Inside</button>
            </Sheet>
          )}
        </>
      )
    }
    render(<Closed />)
    const opener = screen.getByRole('button', { name: 'Open' })
    await userEvent.click(opener)
    expect(screen.getByRole('button', { name: 'Inside' })).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(opener).toHaveFocus()
  })

  it('closes on a backdrop click but not on a click inside', async () => {
    const onClose = vi.fn()
    render(<Harness onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: 'First' }))
    expect(onClose).not.toHaveBeenCalled()
    await userEvent.click(screen.getByTestId('sheet-backdrop'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('locks body scroll while open and restores it after', async () => {
    document.body.style.overflow = 'auto'
    render(<Harness />)
    expect(document.body.style.overflow).toBe('hidden')
    await userEvent.keyboard('{Escape}')
    expect(document.body.style.overflow).toBe('auto')
    document.body.style.overflow = ''
  })

  it('closes when dragged down far enough on touch', () => {
    const onClose = vi.fn()
    render(<Harness onClose={onClose} />)
    const g = grabber()
    expect(g).toHaveClass('cursor-grab')
    fireEvent.pointerDown(g, { pointerType: 'touch', pointerId: 1, clientY: 100 })
    fireEvent.pointerMove(g, { pointerType: 'touch', pointerId: 1, clientY: 180 })
    expect(screen.getByRole('dialog').style.transform).toBe('translateY(80px)')
    fireEvent.pointerUp(g, { pointerType: 'touch', pointerId: 1, clientY: 240 })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('springs back on a short drag and never drags upwards', () => {
    const onClose = vi.fn()
    render(<Harness onClose={onClose} />)
    const g = grabber()
    fireEvent.pointerDown(g, { pointerType: 'touch', pointerId: 1, clientY: 100 })
    fireEvent.pointerMove(g, { pointerType: 'touch', pointerId: 1, clientY: 40 })
    expect(screen.getByRole('dialog').style.transform).toBe('translateY(0px)')
    fireEvent.pointerMove(g, { pointerType: 'touch', pointerId: 1, clientY: 130 })
    fireEvent.pointerUp(g, { pointerType: 'touch', pointerId: 1, clientY: 130 })
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog').style.transform).toBe('')
  })

  it('a data-sheet-close control closes it (animating out) and onClose runs once', async () => {
    const onClose = vi.fn()
    render(
      <Sheet labelledBy="t" onClose={onClose}>
        <button id="t" type="button" data-sheet-close>
          Done
        </button>
      </Sheet>,
    )
    const done = screen.getByRole('button', { name: 'Done' })
    await userEvent.click(done)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledOnce()
    expect(screen.getByRole('dialog')).toHaveAttribute('data-state', 'closed')
  })

  it('ignores mouse drags (drag-to-close is a touch gesture)', () => {
    const onClose = vi.fn()
    render(<Harness onClose={onClose} />)
    const g = grabber()
    fireEvent.pointerDown(g, { pointerType: 'mouse', pointerId: 1, clientY: 100 })
    fireEvent.pointerMove(g, { pointerType: 'mouse', pointerId: 1, clientY: 400 })
    fireEvent.pointerUp(g, { pointerType: 'mouse', pointerId: 1, clientY: 400 })
    expect(onClose).not.toHaveBeenCalled()
  })
})
