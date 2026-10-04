---
id: BRAND-001
title: "Rename the product to Courtside in docs, harness and tools"
epic: EP-70 Dashboard
phase: 7
component: docs
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: []
areas: [CLAUDE.md, README.md, docs/**, tools/**, platform-manifest.yaml]
standards: [documentation, testing]
assignee:
created: 2026-10-04
completed:
---
# BRAND-001 — The product is called Courtside

## Objective
The owner has pivoted from a personal "NBA Fantasy Decision Assistant" to **Courtside**, a fantasy app and simulator
that other people use (D-73, name approved). Every place that names the old concept in docs and the harness (README,
CLAUDE.md, the project spec, runbooks that describe the product, the tools' user-agent string) now says Courtside, and a
test stops the old name from creeping back. The web UI and API title are BRAND-003. `CLAUDE.md` is a Tier B file: this
whole task is `review`, so the owner merges it. Identifiers that name real cloud resources or Python packages are **not** renamed here (D-73 policy):
renaming them would destroy and recreate infrastructure for no user-visible gain.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-73 (name and identifier policy)
- `docs/specification/project-spec.md` §1 (positioning) and `README.md`
- `platform-manifest.yaml` (the header comment calls the domain "NBA fantasy")

## What changes, and what does not
| Changes (user-visible or describes the product) | Stays (an identifier, listed in D-73) |
|---|---|
| `CLAUDE.md` title and first paragraph, `README.md`, `docs/specification/project-spec.md` title and positioning | Python package names `fantasy_*`, the uv workspace layout |
| `tools/yahoo_login.py` `USER_AGENT` text (the product name part; the version and "personal, non-commercial" stay) | GCP project ids `nbafa-*`, bucket and dataset names, Terraform resource names and state |
| runbooks and guides that say "the assistant" about the product | the GitHub repository name and the Python distribution name (BRAND-002) |
| `platform-manifest.yaml` header comment | historical records: research notes, past decisions, task histories, `yahoo-application.md` (a dated artefact, gets a banner) |
| the web UI and API title | _moved to BRAND-003_ |

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Contributor or future Claude session | "docs describe what the product is now" | `CLAUDE.md` still reads as an index and stays under its size; links and anchors still resolve |
| Reader of an old decision or research note | "history is not rewritten" | files in the allow-list keep the old wording; each gets no edit, except the Yahoo application which gets a dated banner |

## Acceptance criteria
- [ ] AC1: no tracked file outside the allow-list contains "Fantasy Assistant", "Fantasy Decision Assistant" or
      "decision-support" used for the product. The allow-list is a short file (`tools/brand_allowlist.txt`) of
      historical paths, each with a reason.
      Verify: `uv run pytest -q tools/tests/test_brand.py` (greps `git ls-files` outside `apps/`, which BRAND-003 adds to
      the scope; also fails if an allow-list entry no longer exists or no longer matches, so the list cannot rot)
- [ ] AC2: the `USER_AGENT` in `tools/yahoo_login.py` names Courtside once, in one place (BRAND-002 changes only the
      repository and package names, not this string).
      Verify: `grep -rn "USER_AGENT *=" tools` shows one line containing "Courtside"; `uv run pytest -q tools/tests`
- [ ] AC3: `docs/specification/project-spec.md` and `README.md` describe Courtside as a fantasy app and simulator
      (accounts, leagues, practice drafts, season replay, valuations) and still state that live Yahoo data is
      owner-only. `CLAUDE.md` is updated the same way and stays an index (no new long sections).
      Verify: `git diff --stat` reviewed by the reviewer subagent; `python tools/tasks.py validate` passes
- [ ] AC4: no link in the docs breaks and the harness is consistent: `platform-manifest.yaml` header says the domain
      is "Courtside (fantasy basketball)", `manifest_check.py` reports no unclassified file, and any new file is
      classified.
      Verify: `uv run python tools/manifest_check.py` exits 0; `uv run pytest -q tools/tests`
- [ ] AC5: nothing that carries a real resource name changed: a diff guard fails if `infra/terraform/**`,
      `warehouse/profiles.yml` or a `nbafa-*` string is modified by this task.
      Verify: `git diff origin/main --stat -- infra warehouse .github` is empty

## Test requirements
`tools/tests/test_brand.py` (grep over tracked files, allow-list hygiene). No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified after the owner's pivot message (fantasy app and simulator, name "Courtside").

## Decisions
- Rename the product, not the plumbing: package and cloud identifiers stay (D-73). BRAND-002 covers the repository.

## Known issues
_None._

## Follow-ups
- BRAND-003 renames the product in the web app and the API title.
- BRAND-002 renames the GitHub repository and the local folder (owner step; WIF trusts the repository **id**, so it
  survives a rename).
- A logo and favicon are a design task (WEB-0xx) and out of scope here; the wordmark stays text.
