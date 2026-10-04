---
id: WEB-039
title: "Player images only when licensed: initials and team colours otherwise"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [DATA-039]
areas: [apps/web/src/features/players/**, apps/web/src/features/draft/**, apps/web/src/features/replay/**, apps/web/src/components/ui/Avatar.tsx, apps/web/src/components/ui/Avatar.test.tsx, apps/web/src/api/**, apps/web/e2e/**, apps/web/firebase.json]
standards: [frontend, testing, design-language]
assignee:
created: 2026-10-04
completed:
---
# WEB-039 — No unlicensed photos on the public site

## Objective
Today every player row hotlinks a cdn.nba.com headshot (`headshotUrl`). That is fine for the owner's private use and not
for other users or ads. The app asks the API whether player images are allowed (`features.playerImages`, DATA-039); when
they are not, it shows the player's initials on a team-colour chip and makes no request to cdn.nba.com. Team logos are
never used.

## Context to read (only these)
- `docs/research/player-images-and-data-licensing.md`; `apps/web/src/features/players/format.ts`
- `apps/web/src/components/ui/Avatar.tsx`; the design-language `Avatar` entry

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner (personal licence) | "I still see headshots" | image fails to load: initials fallback as today |
| Signed-out or other user | "I see a clean initials badge" | no request leaves for cdn.nba.com; no layout shift between the two modes |
| Colour-blind user, dark mode | "the chip is readable" | text/background contrast at least 4.5:1 in both themes for all 30 team colours; initials carry the identity, colour does not |
| Players with the same initials | "which JJ is this" | the name is always in text next to the badge or is the accessible name |
| Config call fails | fail closed | treated as `playerImages: false` |

## Acceptance criteria
- [ ] AC1: `Avatar`/`headshotUrl` use the NBA image only when `features.playerImages` is true; otherwise render initials on
      a team-colour chip (30 teams, table in one file).
      Verify: `corepack pnpm@10 --dir apps/web test -- Avatar`
- [ ] AC2: with images off, a Playwright run on `/players`, `/draft/practice` and `/replay` makes zero requests to
      `cdn.nba.com`; with images on, the existing assertions still pass.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "player-images"`
- [ ] AC3: contrast of every team chip is at least 4.5:1 in light and dark.
      Verify: `corepack pnpm@10 --dir apps/web test -- teamColours` (computes the ratios)
- [ ] AC4: a config failure renders the image-free mode.
      Verify: `corepack pnpm@10 --dir apps/web test -- Avatar` (case "config error")

## Test requirements
Unit tests for Avatar and the colour table; one e2e network assertion.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Created after the owner chose free play with no paid licensing for now.

## Decisions
- Fail closed: no config means no photos.

## Known issues
- `firebase.json` still allows `cdn.nba.com` in `img-src` while the owner uses headshots. The public-launch build removes it (SEC-002 checks).

## Follow-ups
- Optional: Wikimedia Commons images with an attribution page (about 45 % coverage; see the research note).
