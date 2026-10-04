# Web app (`apps/web`)

A mobile-first React SPA for the fantasy assistant (frontend standard; WEB-000 picks: Today B, Matchup A, Waivers A).

- Stack: React 19, Vite, TypeScript (strict), React Router, TanStack Query, Tailwind CSS, Vitest + Testing Library.
- Data: `src/api/` is the only layer that fetches. Until the API and its generated client exist (APP-002/003), it serves **sample fixtures** (`src/api/fixtures.ts`) behind the same `ApiClient` interface.
- Theme: tokens in `src/index.css`; light/dark follows the phone.

```
just web install   # once
just web dev       # http://localhost:5173
just web test      # unit + page tests
just web lint; just web typecheck; just web build
```
