---
id: SEC-001
title: "Pre-publication audit, then make the repo public"
epic: EP-10 Foundation
phase: 1
component: security
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [FND-005, FND-006]
areas: [.github/**, docs/**]
standards: [security, documentation]
assignee: claude
created: 2026-09-24
completed: 2026-10-04
---
# SEC-001 — Pre-publication audit, then make the repo public

## Objective
Make the repository safe to publish (D-38 / G-01 C), then publish it and enable free server-side branch protection.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-38
- `docs/standards/security.md`

## Acceptance criteria
- [x] AC1: gitleaks scan of the **full git history** is clean (or findings rotated and purged, with owner approval)
      Verify: `gitleaks detect --source . --log-opts=--all --redact` reports `no leaks found`
- [x] AC2: No real league data, manager names, emails, or league IDs in any committed file or fixture (scrubber check + grep list recorded)
      Verify: `git grep` for emails, Yahoo league keys and `league_id` in the tree finds only `example.*` and service-account addresses; the Yahoo import fixtures are labelled SYNTHETIC with league ID `00000`
- [x] AC3: No personal information about the owner beyond what they approve (name/handle in README, etc.)
      Verify: the tree and the history contain no owner email other than the GitHub noreply address (the public repo is a fresh single-commit snapshot, G-36 Q1 A; the old history stays in the private archive repo)
- [x] AC4: LICENSE chosen by the owner (PolyForm Noncommercial 1.0.0 chosen in G-36 Q2) and a README for public readers (what it is, a link to the case study)
      Verify: `LICENSE` starts with a `Required Notice:` line and the PolyForm Noncommercial 1.0.0 text; `README.md` has no "planning complete" status and links the licence
- [x] AC5: The owner explicitly confirms publication (outward-facing action); the repo is set public; rulesets enabled on `main` (required CI checks, no force-push)
      Verify: the owner's reply "Yes publish" is in the history; `gh repo view --json visibility` says PUBLIC and `gh api repos/{owner}/{repo}/rulesets` lists the `main` ruleset

## Test requirements
The audit commands and their outputs are recorded in this file.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | command | `gitleaks detect --source . --log-opts="--all" --redact` (v8.30.0 from the pre-commit cache): 484 commits, 8.73 MB | no leaks found |
| AC2 | command | `git grep -IEo` for email addresses (only `example.com/.test/.org`, `noreply@anthropic.com`, GCP service accounts); `git grep` for `nba.l.<n>`, `<n>.l.<n>`, `league_id` values (none); fixtures `packages/ingest/tests/fixtures/yahoo_import/*` start "SYNTHETIC", League ID `00000`; tracked files matching secret/credential/token/tfstate/csv are task docs, `*.tfvars.example` and `warehouse/seeds/availability_overrides.csv` | pass |
| AC3 | command | Audit of the old history: 402 of 543 commits authored with the owner's university student-ID email, 4 commits containing the personal email. Fix: a fresh snapshot (G-36 Q1 A). On the snapshot: `git log --format='%an <%ae>%n%cn <%ce>'` shows only the GitHub noreply address; a `git grep -I` for the two addresses and the student ID finds nothing; gitleaks `--no-git` on the tree is clean | pass |
| AC4 | file | `LICENSE` (PolyForm Noncommercial 1.0.0 with a Required Notice line); `README.md` rewritten for public readers (what it is, parts, privacy, licence) | pass |
| AC5 | owner | owner replied "Yes publish" to G-36 Q3 (2026-10-04); repo created public, `main` ruleset recreated (required checks, no force-push, PRs only); see history | pass |

## Implementation history
- 2026-10-04 — Audit run in worktree `nba-sec001` (AC1-AC3 above). The history holds the owner's university student-ID
  email as the author of 402 commits and the personal email in 4 commits, so publishing the current history is not acceptable.
  Options and a recommendation (a fresh-snapshot public repo, with the current repo kept private as the archive) are in
  gate G-36. Not rewriting history without the owner's decision.
- 2026-10-04 — Owner chose A fresh snapshot, PolyForm Noncommercial, publish. Snapshot built from main plus the open task branches; LICENSE and README added; one orphan commit under the noreply identity; old repo renamed to the private archive.

## Decisions
- G-36 (2026-10-04): fresh single-commit public repo under the GitHub noreply identity; the previous repo is kept private as the archive (full history, hidden PR refs included). Licence PolyForm Noncommercial 1.0.0.

## Known issues
- Resolved by the fresh snapshot: the 2026-09-28 note about the email in the old history no longer applies to the public repo.


## Follow-ups
- The Workload Identity condition pins the old numeric repository id: owner runs `terraform apply` on `infra/terraform/bootstrap` with the new id, then sets the `CLOUD_RUN_ENABLED` and `FIREBASE_ENABLED` repository variables to true.
- Add the case-study link to the README when it exists.
