import { fireEvent, render, screen } from '@testing-library/react'
import { Avatar, initials } from './Avatar'
import { Badge } from './Badge'
import { PageHeader } from './PageHeader'
import { Skeleton } from './Skeleton'

describe('Skeleton (AC3)', () => {
  it('is a decorative shimmer block', () => {
    const { container } = render(<Skeleton className="h-16" />)
    const s = container.firstElementChild as HTMLElement
    expect(s).toHaveClass('skeleton', 'h-16')
    expect(s).toHaveAttribute('aria-hidden', 'true')
  })
})

describe('Badge (AC3)', () => {
  it.each([
    ['neutral', 'bg-surface-2'],
    ['accent', 'bg-accent-tint'],
    ['win', 'text-win'],
    ['lose', 'text-lose'],
    ['warn', 'text-warn'],
  ] as const)('%s tone carries words, not only colour', (tone, cls) => {
    render(
      <Badge tone={tone} icon="!">
        Questionable
      </Badge>,
    )
    const b = screen.getByText('Questionable')
    expect(b).toHaveClass(cls)
    expect(b.querySelector('[aria-hidden="true"]')).toHaveTextContent('!')
  })
})

describe('Avatar (AC3)', () => {
  it('shows the image, then the initials when it fails', () => {
    const { container } = render(<Avatar src="https://x/1.png" name="Nikola Jokić" size={40} />)
    const img = container.querySelector('img') as HTMLImageElement
    expect(img.src).toBe('https://x/1.png')
    expect(img).toHaveStyle({ width: '40px', height: '40px' })
    fireEvent.error(img)
    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByText('NJ')).toBeInTheDocument()
  })

  it('tries again when the source changes', () => {
    const { container, rerender } = render(<Avatar src="https://x/1.png" name="A B" size={40} />)
    fireEvent.error(container.querySelector('img') as HTMLImageElement)
    rerender(<Avatar src="https://x/2.png" name="C D" size={40} />)
    expect(container.querySelector('img')?.src).toBe('https://x/2.png')
  })

  it.each([
    ['Nikola Jokić', 'NJ'],
    ['Shai Gilgeous-Alexander', 'SG'],
    ['Nenê', 'N'],
    ['  ', ''],
  ])('initials(%s) = %s', (name, want) => {
    expect(initials(name)).toBe(want)
  })
})

describe('PageHeader (AC3)', () => {
  it('renders a large title, an eyebrow and a trailing slot', () => {
    render(<PageHeader title="Waivers" eyebrow="Thu 1 Oct" trailing={<span>Sample</span>} />)
    const h = screen.getByRole('heading', { level: 1, name: 'Waivers' })
    expect(h).toHaveClass('text-title-lg')
    expect(screen.getByText('Thu 1 Oct')).toHaveClass('text-subhead')
    expect(screen.getByText('Sample')).toBeInTheDocument()
  })
})
