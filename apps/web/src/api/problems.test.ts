import { describe, expect, it } from 'vitest'
import { ApiError } from './http'
import { problemOf } from './problems'

const api = (status: number, type: string) => new ApiError(status, `/problems/${type}`, 'x')

describe('problemOf (WEB-016 AC2)', () => {
  it.each([
    [api(404, 'no-brief'), 'not-ready', 'none'],
    [api(404, 'no-players'), 'not-ready', 'none'],
    [api(404, 'no-matchup'), 'no-matchup', 'none'],
    [api(404, 'not-found'), 'updating', 'retry'], // the site is ahead of the API
    [api(401, 'unauthenticated'), 'unauthenticated', 'sign-in'],
    [api(403, 'forbidden'), 'forbidden', 'sign-out'],
    [api(429, 'rate-limited'), 'rate-limited', 'retry'],
    [api(500, 'internal'), 'server', 'retry'],
    [api(503, 'snapshot-schema'), 'server', 'retry'],
    [api(418, 'something-new'), 'server', 'retry'], // unknown problems fall back
    [new Error('boom'), 'server', 'retry'],
  ])('maps %s to %s', (err, kind, action) => {
    const p = problemOf(err, true)
    expect(p.kind).toBe(kind)
    expect(p.action).toBe(action)
  })

  it('a failed fetch is "can’t reach the server" online and "offline" offline', () => {
    expect(problemOf(new TypeError('Failed to fetch'), true).title).toBe('Can’t reach the server')
    expect(problemOf(new TypeError('Failed to fetch'), false).kind).toBe('offline')
    expect(problemOf(api(500, 'internal'), false).kind).toBe('offline')
  })

  it('never puts a status code or stack in the headline', () => {
    for (const s of [401, 403, 429, 500, 503]) {
      expect(problemOf(api(s, 'x'), true).title).not.toMatch(/\d{3}|Error|at /)
    }
  })
})
