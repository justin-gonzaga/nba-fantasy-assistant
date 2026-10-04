---
id: YAHOO-002
title: "Retire the Yahoo import, login and Yahoo-derived values (after the 18 Oct draft)"
epic: EP-20 Ingestion
phase: 7
component: pipeline
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: [DRAFT-006]
areas: [packages/ingest/src/fantasy_ingest/yahoo_import.py, packages/ingest/src/fantasy_ingest/__init__.py, packages/ingest/tests/test_yahoo_import.py, tools/yahoo_login.py, tools/tests/test_yahoo_login.py, tools/doctor.py, apps/pipeline/src/fantasy_pipeline/**, apps/pipeline/tests/**, packages/core/src/fantasy_core/league.py, packages/core/src/fantasy_core/settings.py, packages/core/tests/test_settings.py, packages/models/src/fantasy_models/valuation.py, packages/models/src/fantasy_models/preseason/schema.py, infra/terraform/modules/env/serving.tf, apps/web/src/auth/Landing.tsx, docs/**]
standards: [software-engineering, data-engineering, testing, documentation]
assignee:
created: 2026-10-04
completed:
---
# YAHOO-002 — Courtside does not depend on Yahoo

## Objective
The owner decided (2026-10-04) that Courtside is its own fantasy app and will not rely on Yahoo at all. The real draft on
Sun 18 Oct is still played in a Yahoo league, so nothing is removed before DRAFT-006 (the dry run) and the draft are done.
Afterwards this task removes the Yahoo login, the assisted import, the Yahoo-fed values and the Yahoo secrets, keeps the
scoring *formats* (they are Courtside's own concept now, ADR-0018), and makes sure nothing a user sees is derived from
Yahoo data. Raw Yahoo snapshots on disk stay (bronze is immutable) but are not read by the product.

## Context to read (only these)
- `docs/research/yahoo-api.md` (what was stored and why); `docs/project/human-approval-gates.md` G-04
- `grep -rli yahoo` over `apps packages tools infra` (the inventory in AC1)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner after the draft | "no Yahoo anywhere in the app" | the draft board and replay still build from NBA data and the format rules alone |
| Public user | "nothing I see comes from Yahoo" | market values from Yahoo (DATA-034) are not an input to any public value; if one is, it is replaced or removed |
| Scoring format | "H2H 9-cat still works" | format names stay; the parser takes a plain settings object, not a Yahoo page |
| Yahoo-owned names in history | "old results" | past reports keep their text; the code path is gone, not the evidence |
| Secrets and infra | "no orphaned secret" | the Yahoo secret references in Terraform are removed in a Tier B plan the owner applies |

## Acceptance criteria
- [ ] AC1: an inventory lists every Yahoo reference in `apps packages tools infra` with the decision per item
      (remove / rename to a neutral name / keep as a historical record).
      Verify: `docs/project/yahoo-retirement-inventory.md` exists, and `grep -rli yahoo apps packages tools infra` after the task lists only items marked keep
- [ ] AC2: league scoring settings are entered through a plain settings object (no Yahoo page parsing needed to run the draft or replay).
      Verify: `uv run pytest -q apps/pipeline/tests packages/core/tests`
- [ ] AC3: no input to a public value derives from Yahoo data; where a Yahoo-derived market value was used it is removed and the evaluation reports are regenerated or marked superseded.
      Verify: `uv run pytest -q packages/models/tests -k valuation`; the PR lists each affected report
- [ ] AC4: the Yahoo login tool, import module, their tests and the doctor checks are deleted; `just check` passes.
      Verify: `just check` exits 0
- [ ] AC5: the Terraform plan removes the Yahoo secret references and shows no other change (the owner applies it).
      Verify: `terraform -chdir=infra/terraform/envs/dev plan` output pasted in the PR

## Test requirements
Existing suites must pass after deletion; no new behaviour.

## Evaluation requirements
Regenerate only the reports whose inputs changed (AC3).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Created from the owner's decision to drop Yahoo reliance entirely.

## Decisions
- Delete code, keep bronze: raw data is immutable and may still be used for private research.

## Known issues
_None._

## Follow-ups
- G-04 (Yahoo retention) becomes moot once no Yahoo data is read; close it as superseded.
