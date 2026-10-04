---
id: FND-001
title: "Install developer toolchain (uv, just, gh, gcloud, Terraform)"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: gated
gate: G-12
depends_on: []
areas: [docs/guides/local-development.md]
standards: [devops]
assignee: claude
created: 2026-09-24
completed: 2026-09-25
---
# FND-001 — Install developer toolchain (uv, just, gh, Docker Desktop)

## Objective
Get the laptop ready: uv, just, gh, gcloud and Terraform installed and on PATH (tools approved in stack round 1 and the infra round; G-12 A: Claude installs the CLI tools). Docker Desktop is the owner's install, moved to FND-016.

## Context to read (only these)
- `docs/project/human-approval-gates.md` G-12

## Acceptance criteria
- [x] AC1: uv, just, gh, gcloud and Terraform are installed, and each reports a version in a **new** shell.
      Verify: new PowerShell → `uv --version; just --version; gh --version; gcloud --version; terraform --version` → 5 version lines, no errors
- [x] AC2: uv can provision the project's Python version.
      Verify: `uv python find 3.13` → prints a Python 3.13 path
- [x] AC3: The install steps (IDs, commands, and what the owner does manually) are recorded so a clean machine can repeat them.
      Verify: `docs/guides/local-development.md` §Prerequisites lists every command used here

## Test requirements
No code. Verification commands only.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | fresh-env PowerShell (PATH reloaded from registry), 2026-09-25 | uv 0.12.18 · just 1.58.0 · gh 2.101.0 · Google Cloud SDK 586.0.0 · Terraform v1.16.2 |
| AC2 | command | `uv python find 3.13` | a Python 3.13 path is printed (Microsoft Store Python; FND-002 pins a uv-managed interpreter) |
| AC3 | report | docs/guides/local-development.md §1–2 | every winget/uv command used is listed, plus macOS/Linux equivalents and troubleshooting |

## Implementation history
### 2026-09-25 — session 1
- Refined the ACs to the task spec standard; split Docker Desktop into FND-016 (owner).
- Installed via winget: astral-sh.uv, GitHub.cli, Hashicorp.Terraform, Google.CloudSDK (UAC prompt); `uv tool install rust-just`; `uv tool update-shell`.
- Gotcha: the current shell doesn't see the new PATH until restarted. Verified with the PATH reloaded from the registry.
- Attempts: 2 (the first `just` install failed because uv wasn't on PATH yet). Skills: work-task flow. Interventions: none (the owner installed Docker + WSL separately).

## Decisions
- 2026-09-24: Docker Desktop moved to FND-016 (an owner action, needed from FND-015), so this task isn't blocked on the owner.

## Known issues
_None._

## Follow-ups
_None._
