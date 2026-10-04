---
id: ANL-009
title: "Late-season availability: stars on bottom teams sit in March (fantasy playoffs)"
epic: EP-30 Semantics
phase: 6
component: models
status: todo
ready: false
size: M
autonomy: gated
gate: G-19
depends_on: [RSCH-008]
areas: [packages/models/**, packages/decision/**, packages/evaluation/**, apps/pipeline/**]
standards: [ml, testing]
assignee:
created: 2026-10-03
completed:
---
# ANL-009 — Late-season availability adjustment

## Objective
RSCH-008 Q2 (pre-registered, 2015-16 … 2025-26 without the COVID seasons) found material late-season effects after
1 Mar, which is exactly the owner's fantasy playoffs (weeks 18–20, 1–21 Mar):
- stars on bottom-6 teams miss **+6.2 extra games** (95 % CI +4.57 to +7.72); rotation players on bottom-6 teams +3.72 (CI +2.84 to +4.69);
- stars on contenders miss **+2.4** extra games (CI +1.49 to +3.32), resting before the playoffs;
- players ≤ 23 on bottom-6 teams gain **+4.3 mpg** (CI +3.69 to +4.99).
The in-season availability model (base rates from the injury report) doesn't know any of this. This task will adjust
week-ahead availability (and the waiver/stream recommendations) for late-season team context, and, for the draft,
weigh whether to discount stars likely to be on bottom teams.

## Acceptance criteria
_To be refined (ready: false), pre-registered before any model run (ML standard; gate G-19 covers in-season methods):
candidate = base availability × a context factor from RSCH-008's effect table, re-estimated leak-free per season;
evaluation = the walk-forward availability/brier check on the 2025-26 holdout second half; ship rule pre-registered._

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-03 — Created from RSCH-008 Q2's pre-registered "material" rule.

## Decisions
_None yet._

## Known issues
- Team context on 1 Mar is a league-wide win-% proxy (no conference data in the logs); a standings source would sharpen it.

## Follow-ups
_None._
