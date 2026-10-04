import { describe, expect, it } from 'vitest'
import { ApiError, httpClient } from './http'
import { sampleWaivers } from './fixtures'

function fakeFetch(status: number, body: unknown, seen: string[] = []): typeof fetch {
  return (input) => {
    seen.push(String(input))
    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status,
        headers: { 'content-type': 'application/json' },
      }),
    )
  }
}

describe('httpClient', () => {
  it('reads a view from the API base URL', async () => {
    const seen: string[] = []
    const client = httpClient('https://example.test/api/', fakeFetch(200, sampleWaivers, seen))
    expect(await client.waivers()).toEqual(sampleWaivers)
    expect(seen).toEqual(['https://example.test/api/waivers'])
  })

  it('turns a problem+json response into an ApiError with its title', async () => {
    const problem = { type: '/problems/no-brief', title: 'No brief published', status: 404 }
    const client = httpClient('https://example.test', fakeFetch(404, problem))
    const err = await client.today().catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({
      status: 404,
      type: '/problems/no-brief',
      message: 'No brief published',
    })
  })

  it('keeps a status-based message when the error body is not JSON', async () => {
    const html: typeof fetch = () =>
      Promise.resolve(new Response('<html>Bad gateway</html>', { status: 502 }))
    const err = await httpClient('https://example.test', html)
      .matchup()
      .catch((e: unknown) => e)
    expect(err).toMatchObject({ status: 502, message: 'Request failed (502)' })
  })
})
