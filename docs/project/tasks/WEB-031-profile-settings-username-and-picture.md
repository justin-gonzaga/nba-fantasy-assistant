---
id: WEB-031
title: "Profile settings: username, profile picture and public profile preview"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-013, WEB-014, WEB-030]
areas: [apps/web/src/settings/**, apps/web/src/components/avatar/**, apps/web/e2e/profile*.spec.ts]
standards: [frontend, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-031 — Profile section of the settings page

## Objective
Extend the settings page (WEB-014) with a Profile section: change username (30-day cooldown), upload, crop-preview and
remove a picture, and see exactly what other people see. One avatar component serves every place a picture appears
(profile, team, member lists, league cards), with the initials/preset fallback, so there is a single implementation.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5, §9
- `apps/web/src/settings/*` (WEB-014), the design language standard

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member | "I set a profile picture" | choose from files or camera roll; client-side preview with square crop; client checks type and size (2 MB) before upload but the server remains the authority; progress and cancel; server rejection shown with the reason |
| Member without a picture | "I still look good" | initials avatar in a colour from the username, or one of 12 preset icons; contrast meets WCAG AA |
| Member changes name | "new username" | live availability, cooldown message with the date, the old name is reserved note, If-Match conflict handled by reload |
| Member removes picture | "no picture" | confirmation, immediate fallback, no flash of the old image (cache-busting id) |
| Slow phone network | resilient | upload retries once, keeps the form state; leaving the page mid-upload warns |
| Hidden picture (reported) | honest | shows the fallback and a note "this picture is under review" to the owner of it only |
| Screen reader | accessible | file input labelled, preview has alt text "Your profile picture", errors announced |
| Public preview | "what do others see?" | a card showing username, avatar and nothing else, matching the API's public fields |

## Acceptance criteria
- [ ] AC1: Profile section: username edit with availability and cooldown, picture upload/replace/remove, and a
      "what others see" preview.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep profile`
- [ ] AC2: one `Avatar` component is used for every avatar in the app; a lint rule (or a test grep) fails if an
      `<img>` for a profile picture is rendered anywhere else.
      Verify: `corepack pnpm@10 --dir apps/web test src/components/avatar`; `grep -rn "avatar" apps/web/src --include=*.tsx`
      shows only `Avatar` usage sites
- [ ] AC3: client-side pre-checks (type, size, dimensions) give instant messages; every server problem code from
      APP-013 maps to a human sentence (table-driven test over the problem codes in the OpenAPI document).
      Verify: `corepack pnpm@10 --dir apps/web test src/settings -t "media problems"`
- [ ] AC4: fallback avatars meet contrast AA in both themes for all 12 colours and the 12 presets.
      Verify: `test:e2e --grep a11y` plus a unit test computing contrast for the palette
- [ ] AC5: works at 320 px and with the keyboard only; axe is clean.
      Verify: `test:e2e --grep "profile.*(phone|a11y)"`

## Test requirements
Component tests for the avatar and the uploader (mocked API); Playwright against the API emulator or the MSW layer.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- The "other people see" preview is generated from the same public-profile type as the API, so it cannot drift.

## Known issues
_None._

## Follow-ups
_None._
