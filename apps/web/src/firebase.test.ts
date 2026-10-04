import firebase from '../firebase.json'

// WEB-012 AC2: the hosting config serves the SPA with safe headers and sane caching.
type Header = { key: string; value: string }
type Rule = { source: string; headers: Header[] }
const config = firebase as {
  hosting: { public: string; rewrites: { source: string; destination: string }[]; headers: Rule[] }
}

const headersFor = (source: string) =>
  Object.fromEntries(
    (config.hosting.headers.find((r) => r.source === source)?.headers ?? []).map((h) => [
      h.key,
      h.value,
    ]),
  )

describe('firebase.json', () => {
  it('serves the built SPA and falls back to index.html for client routes', () => {
    expect(config.hosting.public).toBe('dist')
    expect(config.hosting.rewrites).toEqual([{ source: '**', destination: '/index.html' }])
  })

  it('sets security headers on every response', () => {
    const all = headersFor('**')
    const csp = all['Content-Security-Policy'] ?? ''
    expect(csp).toContain("default-src 'self'")
    expect(csp).toContain("frame-ancestors 'self'") // only the site's own sign-in handler frames it
    expect(csp).not.toContain("'unsafe-inline' 'unsafe-eval'")
    expect(csp).not.toMatch(/script-src[^;]*'unsafe-inline'/)
    expect(all['Strict-Transport-Security']).toMatch(/max-age=\d+/)
    expect(all['X-Content-Type-Options']).toBe('nosniff')
  })

  it('lets Google sign-in and the API work, and nothing broader (WEB-013)', () => {
    const csp = headersFor('**')['Content-Security-Policy'] ?? ''
    const directive = (name: string) =>
      csp
        .split(';')
        .map((d) => d.trim())
        .find((d) => d.startsWith(`${name} `))
        ?.split(/\s+/)
        .slice(1) ?? []
    expect(directive('script-src')).toEqual(["'self'", 'https://apis.google.com'])
    expect(directive('connect-src')).toEqual(
      expect.arrayContaining([
        'https://identitytoolkit.googleapis.com',
        'https://securetoken.googleapis.com',
        'https://api-yzyagkwnaa-ts.a.run.app',
      ]),
    )
    expect(directive('connect-src')).not.toContain('https:')
    // Google profile photos and NBA headshots (WEB-005), nothing broader
    expect(directive('img-src')).toEqual([
      "'self'",
      'data:',
      'https://lh3.googleusercontent.com',
      'https://cdn.nba.com',
    ])
    expect(directive('frame-src')).toEqual(
      expect.arrayContaining(['https://accounts.google.com', 'https://apis.google.com']),
    )
  })

  it('caches hashed assets for a year and never caches index.html', () => {
    expect(headersFor('/assets/**')['Cache-Control']).toContain('immutable')
    expect(headersFor('/index.html')['Cache-Control']).toBe('no-cache')
  })
})
