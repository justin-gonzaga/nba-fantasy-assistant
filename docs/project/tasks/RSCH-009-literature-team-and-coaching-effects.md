---
id: RSCH-009
title: "Literature: do teams and coaches change individual player production?"
epic: EP-15 Draft assistant
phase: 7
component: evaluation
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [docs/research/**]
standards: [ml]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# RSCH-009 — Literature: team and coaching effects on individual production

## Objective
The owner (2026-10-03) wants to know whether a player's **team or coaching staff** changes his output enough that
modelling it would beat the current projection (H1+aging+M1). Before any data work, collect what is known and
verified, so ANL-010 tests the effects the literature says are real and sizes its expectations. Cite, don't
re-research: R-86 (mid-season coaching changes, team-level only) and the R-xx in `lit-breakouts.md` §3 are the
starting point.

## Context to read (only these)
- `docs/research/lit-breakouts.md` (topic 3, R-86, Gaps); `docs/research/ml-literature-review.md` (index only)

## Questions (each answered with verified [R-xx] or marked "no source found")
1. **Pace / possessions**: how much do counting stats scale with team pace; is pace a team or a coach trait?
2. **Usage and role redistribution**: when a high-usage teammate leaves or arrives, how are shots and assists
   redistributed (the "usage curve")?
3. **Coaching**: effects of a head-coach change on an *individual's* minutes, usage, 3PA rate, rebounding
   (scheme) or rotation depth; whether coach tendencies persist across teams.
4. **Team effects in player ratings**: variance decomposition, mixed models or adjusted plus-minus work that
   separates player from team context; how large the team share is for box-score rates.
5. **Player movement (trades, free agency)**: production change after changing teams vs regression to the mean.
6. **Method**: designs that separate a context effect from selection (who gets traded) and from regression to
   the mean (event studies, synthetic controls, movers designs from labour economics).

## Acceptance criteria
- [x] AC1: `docs/research/lit-team-effects.md` has ≥ 8 new entries in the R-xx table format of
      `ml-literature-review.md`, each with its access level (full text / abstract) and how it applies.
      Verify: file exists; entries carry Verified/Unverified tags; `python tools/tasks.py validate` passes
- [x] AC2: a "What this means for ANL-010" section: the effects worth testing, expected magnitudes with sources,
      and the confounders each must handle.
      Verify: section present; every claim cites an R-xx
- [x] AC3: a Gaps section (questions with no source found), as in `lit-breakouts.md`.
      Verify: section present

## Test requirements
n/a (research). The `researcher` subagent does the web work and writes the file.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | doc | `docs/research/lit-team-effects.md` R-110–R-118 (9 entries: 2 full text, 6 abstract, 1 grey-literature full text, flagged) | 8 DOIs confirmed registered via the doi.org handle API (responseCode 1) |
| AC2 | doc | § What this means for ANL-010 | present; claims cite R-xx |
| AC3 | doc | § Gaps | present |

## Implementation history
- 2026-10-03 — Specified from the owner's request (team and coaching effects).
- 2026-10-03 — Done by the `researcher` subagent; DOIs re-checked by the main session. Key points for ANL-010:
  pace scales counting stats (R-110; test per possession first); individual ratings carry teammate context
  (R-113, ~0.66 RPM per point of teammate RPM); coaching effects are real but modest and mostly team-level
  (R-111, R-112); movers/two-way fixed effects and synthetic control are the design templates but have no NBA
  application (R-114, R-115); contract-year effort (~8 % of MP48) is a confound to control (R-116–R-118).
  Follow-up for ANL-010: check movers per team-season before relying on two-way fixed effects (limited-mobility
  bias, noted but not verified against a primary source).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- ANL-010 uses this to choose what to measure.
