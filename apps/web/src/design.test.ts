/// <reference types="node" />
// Guards for the "Courtside" design language (docs/standards/design-language.md §8, WEB-017).
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

// Read from disk: the test runner stubs CSS imports (`css: false`).
const css = readFileSync(join(__dirname, 'index.css'), 'utf8')

/** The body of the first `{ … }` block that starts at `from` (brace-matched). */
function block(source: string, from: number): string {
  const open = source.indexOf('{', from)
  let depth = 0
  for (let i = open; i < source.length; i++) {
    if (source[i] === '{') depth++
    if (source[i] === '}' && --depth === 0) return source.slice(open + 1, i)
  }
  throw new Error('unbalanced braces')
}

const at = (needle: string) => {
  const i = css.indexOf(needle)
  if (i < 0) throw new Error(`index.css has no ${needle}`)
  return block(css, i)
}

const light = at(':root {')
const dark = block(at('@media (prefers-color-scheme: dark)'), 0)
const theme = at('@theme')
const reduced = at('@media (prefers-reduced-motion: reduce)')

const defines = (body: string, token: string) => new RegExp(`(^|[\\s;{])${token}\\s*:`).test(body)

// Tokens that change with the theme: designed for both, never inverted.
const THEMED = [
  '--ground',
  '--surface',
  '--surface-2',
  '--line',
  '--ink',
  '--ink-2',
  '--muted',
  '--accent',
  '--accent-tint',
  '--accent-ink',
  '--win',
  '--lose',
  '--even',
  '--ok',
  '--warn',
  '--button',
  '--button-ink',
  '--raised',
  '--scrim',
  '--shadow-0',
  '--shadow-1',
  '--shadow-2',
  '--shadow-3',
]

// Tokens that are the same in both themes.
const MOTION = [
  '--motion-quick',
  '--motion-base',
  '--motion-sheet',
  '--motion-sheet-out',
  '--stagger',
]
const THEME_SCALE = [
  '--text-display',
  '--text-title-lg',
  '--text-title',
  '--text-headline',
  '--text-body',
  '--text-subhead',
  '--text-caption',
  '--radius-chip',
  '--radius-row',
  '--radius-card',
  '--radius-sheet',
  '--ease-quick',
  '--ease-base',
  '--ease-sheet',
  '--ease-sheet-out',
]

describe('design tokens (AC2)', () => {
  it.each(THEMED)('%s is defined in light and dark', (token) => {
    expect(defines(light, token)).toBe(true)
    expect(defines(dark, token)).toBe(true)
  })

  it.each(MOTION)('motion token %s is defined', (token) => {
    expect(defines(light, token)).toBe(true)
  })

  it.each(THEME_SCALE)('scale token %s is exposed to Tailwind', (token) => {
    expect(defines(theme, token)).toBe(true)
  })

  it('motion durations follow the spec (120 / 220 / 360 / 240 ms, 24 ms stagger)', () => {
    expect(light).toMatch(/--motion-quick:\s*120ms/)
    expect(light).toMatch(/--motion-base:\s*220ms/)
    expect(light).toMatch(/--motion-sheet:\s*360ms/)
    expect(light).toMatch(/--motion-sheet-out:\s*240ms/)
    expect(light).toMatch(/--stagger:\s*24ms/)
  })

  it('dark elevation uses an inner highlight, not only heavier shadows', () => {
    for (const level of ['--shadow-1', '--shadow-2', '--shadow-3']) {
      const value = new RegExp(`${level}:([^;]+);`).exec(dark)?.[1] ?? ''
      expect(value).toMatch(/inset/)
    }
  })

  it('the material falls back to an opaque surface without backdrop-filter', () => {
    const base = at('.material {')
    expect(base).toMatch(/background:\s*var\(--surface\)/)
    expect(base).not.toMatch(/backdrop-filter/)
    const supports = at('@supports')
    expect(supports).toMatch(/backdrop-filter:\s*saturate\(180%\) blur\(20px\)/)
    expect(supports).toMatch(/color-mix\(in oklab, var\(--surface\) 90%, transparent\)/)
  })

  it('the reduced-motion block disables transforms, stagger and shimmer', () => {
    expect(reduced).toMatch(/transform:\s*none\s*!important/)
    expect(reduced).toMatch(/--stagger:\s*0ms/)
    expect(reduced).toMatch(/\.skeleton::after\s*\{[^}]*animation:\s*none/)
    for (const t of ['--motion-base', '--motion-sheet', '--motion-sheet-out'])
      expect(reduced).toMatch(new RegExp(`${t}:\\s*120ms`))
  })

  it('stagger is capped at 8 items', () => {
    expect(css).toMatch(/\.stagger > :nth-child\(n \+ 9\)/)
    expect(css).not.toMatch(/\.stagger > :nth-child\(9\)/)
  })

  it('hover lift and light only apply to fine pointers', () => {
    const hover = at('@media (hover: hover) and (pointer: fine)')
    expect(hover).toMatch(/\.lift:hover/)
    expect(hover).toMatch(/\.light:hover::before/)
    // Outside that media query nothing reacts to :hover (no sticky hover after a tap).
    const outside = css.replace(`@media (hover: hover) and (pointer: fine) {${hover}}`, '')
    expect(outside).not.toMatch(/:hover/)
  })

  it('the light is a radial gradient at --x / --y', () => {
    expect(css).toMatch(/radial-gradient\(\s*240px circle at var\(--x, 50%\) var\(--y, 50%\)/)
  })
})

// Every source file except tests: components must use semantic tokens and primitives.
const sources = import.meta.glob<string>(['./**/*.{ts,tsx}', '!./**/*.test.{ts,tsx}'], {
  query: '?raw',
  import: 'default',
  eager: true,
})

const PALETTE =
  'slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|black|white'
const RAW_PALETTE = new RegExp(
  `\\b(?:bg|text|border|ring|outline|fill|stroke|from|via|to|shadow|decoration|divide|placeholder|caret|accent)-(?:${PALETTE})(?:-\\d+)?(?:/\\d+)?\\b`,
)

function offenders(re: RegExp): string[] {
  return Object.entries(sources)
    .filter(([path]) => !path.endsWith('schema.gen.ts'))
    .flatMap(([path, text]) =>
      text
        .split('\n')
        .map((line, i) => [line, i] as const)
        .filter(([line]) => re.test(line))
        .map(([line, i]) => `${path}:${i + 1}: ${line.trim()}`),
    )
}

describe('pages use tokens and primitives (AC4)', () => {
  it('scans the sources', () => {
    expect(Object.keys(sources).length).toBeGreaterThan(10)
  })

  it('no raw palette classes', () => {
    expect(offenders(RAW_PALETTE)).toEqual([])
  })

  it('no one-off shadows, durations, easings or pulses', () => {
    expect(
      offenders(/\b(?:shadow-(?:2xs|xs|sm|md|lg|xl|2xl|\[)|duration-|ease-\[|animate-)/),
    ).toEqual([])
  })

  it('type sizes come from the scale (no px or default Tailwind sizes)', () => {
    expect(offenders(/\btext-(?:\[\d|xs\b|sm\b|base\b|lg\b|xl\b|\dxl\b)/)).toEqual([])
  })

  it('no hex colours in components', () => {
    expect(offenders(/#[0-9a-fA-F]{3,8}\b['"`;\s)]/)).toEqual([])
  })

  it('figures use tabular UI numerals, not the mono face (WEB-023 AC3)', () => {
    expect(offenders(/\bfont-mono\b/)).toEqual([])
  })
})
