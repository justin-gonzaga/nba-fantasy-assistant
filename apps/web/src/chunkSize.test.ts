import { evaluate, FX_BUDGET_GZIP } from '../scripts/check-chunk-size.mjs'

const draft = { name: 'DraftPracticePage-abc.js', text: 'x exponentialRampToValueAtTime y' }
const entry = { name: 'index-abc.js', text: 'app code' }

describe('chunk size check (DRAFT-020 AC7)', () => {
  it('passes a lazy draft chunk with fx code under budget', () => {
    expect(evaluate([draft, entry], 3000).ok).toBe(true)
  })

  it('fails over the budget, naming the size', () => {
    const r = evaluate([draft, entry], FX_BUDGET_GZIP + 1)
    expect(r.ok).toBe(false)
    expect(r.message).toContain('over the')
  })

  it('fails when the draft room is not a separate chunk', () => {
    const r = evaluate([{ name: 'index-abc.js', text: 'exponentialRampToValueAtTime' }], 100)
    expect(r.ok).toBe(false)
    expect(r.message).toContain('lazy')
  })

  it('fails when the fx code leaks into the entry chunk', () => {
    const r = evaluate([draft, { ...entry, text: 'exponentialRampToValueAtTime' }], 100)
    expect(r.ok).toBe(false)
    expect(r.message).toContain('entry chunk')
  })
})
