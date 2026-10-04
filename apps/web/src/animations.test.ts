/// <reference types="node" />
// DRAFT-020 AC7: animations only change transform and opacity (the compositor-only properties), so a
// lot's motion never triggers layout or paint on a low-end phone.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const css = readFileSync(join(__dirname, 'index.css'), 'utf8')

/** Every `@keyframes name { … }` block, brace-matched. */
function keyframes(): Map<string, string> {
  const found = new Map<string, string>()
  for (const m of css.matchAll(/@keyframes\s+([\w-]+)\s*\{/g)) {
    const open = (m.index ?? 0) + m[0].length - 1
    let depth = 0
    for (let i = open; i < css.length; i++) {
      if (css[i] === '{') depth++
      if (css[i] === '}' && --depth === 0) {
        found.set(m[1] as string, css.slice(open + 1, i))
        break
      }
    }
  }
  return found
}

const ALLOWED = new Set(['opacity', 'transform'])
const frames = keyframes()

describe('animations stay on the compositor (DRAFT-020 AC7)', () => {
  it('finds the keyframes', () => {
    for (const name of ['lot-in', 'price-pop', 'bidder-flash', 'stamp', 'ring-pulse', 'bar-grow'])
      expect(frames.has(name)).toBe(true)
  })

  it.each([...frames.keys()])('%s animates only transform and opacity', (name) => {
    const props = [...(frames.get(name) ?? '').matchAll(/([a-z-]+)\s*:/g)].map((m) => m[1])
    expect(props.length).toBeGreaterThan(0)
    for (const p of props) expect(ALLOWED.has(p as string)).toBe(true)
  })

  it('reduced motion switches the lot animations off', () => {
    const i = css.indexOf('@media (prefers-reduced-motion: reduce)')
    const after = css.slice(i)
    for (const cls of ['.lot-in', '.price-pop', '.ring-pulse', '.bar-grow'])
      expect(after).toContain(cls)
  })
})
