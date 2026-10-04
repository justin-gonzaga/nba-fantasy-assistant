---
id: BRAND-003
title: "Show the name Courtside in the web app and the API title"
epic: EP-70 Dashboard
phase: 7
component: web
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [BRAND-001]
areas: [apps/web/index.html, apps/web/public/**, apps/web/src/components/ui/Sidebar.tsx, apps/web/src/components/ui/Sidebar.test.tsx, apps/web/src/App.tsx, apps/web/e2e/**, apps/web/README.md, apps/api/src/fantasy_api/main.py, apps/api/openapi.json, apps/web/src/api/schema.gen.ts]
standards: [frontend, testing, design-language]
assignee:
created: 2026-10-04
completed:
---
# BRAND-003 — Courtside in the app

## Objective
People who open the site see one product name. The tab title, the sidebar and landing wordmark, the installed-app
manifest name and the API's OpenAPI title say Courtside (D-73, name approved). Package names, cloud resource names and
the repository are unchanged (D-73 policy; BRAND-002 covers the repository). The docs and harness side is BRAND-001.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-73
- the BRAND-001 "what changes and what does not" table

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| New visitor on the landing page | "I see one clear product name" | the wordmark, tab title and share preview agree; no old name at 320 px (no sidebar) or on desktop |
| Owner with the installed home-screen icon | "the app is called Courtside" | the manifest `name` and `short_name` are updated; the old name goes away after one load |
| Screen reader | "the brand reads once" | the wordmark has one accessible name, no duplicated text between logo and title |
| Developer reading the API docs | "the API says what it is" | the OpenAPI title is "Courtside API" and the generated client is regenerated with no diff on a second run |

## Acceptance criteria
- [ ] AC1: the tab title, sidebar wordmark, landing wordmark and manifest name read "Courtside"; the existing e2e
      wordmark assertions are updated, not deleted.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "landing|desktop|phone"` passes with an assertion that
      `document.title === "Courtside"`
- [ ] AC2: the API title is "Courtside API" and the generated client has no diff on a second run.
      Verify: `just api-client` twice, `git diff --exit-code apps/api/openapi.json apps/web/src/api/schema.gen.ts`
- [ ] AC3: the wordmark has one accessible name (axe clean at 320 px and 1280 px).
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "a11y"`
- [ ] AC4: no tracked file under `apps/` outside the allow-list contains the old product name (the BRAND-001 test covers
      `apps/` once this task merges).
      Verify: `uv run pytest -q tools/tests/test_brand.py`

## Test requirements
Updated Playwright specs, the OpenAPI regeneration check. No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Split out of BRAND-001 in review (the original task spanned docs, harness, web and API).

## Decisions
- Rename the product, not the plumbing (D-73).

## Known issues
_None._

## Follow-ups
- A logo and favicon are a design task, out of scope; the wordmark stays text.
