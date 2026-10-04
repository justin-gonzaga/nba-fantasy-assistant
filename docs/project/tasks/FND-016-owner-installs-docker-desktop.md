---
id: FND-016
title: "Owner installs Docker Desktop"
epic: EP-10 Foundation
phase: 1
component: tooling
status: todo
ready: true
size: S
autonomy: gated
gate: G-12
depends_on: []
areas: [docs/guides/local-development.md]
standards: [devops]
assignee: owner
created: 2026-09-24
completed:
---
# FND-016 — Owner installs Docker Desktop

## Objective
Docker Desktop is needed for the container image (FND-015). It needs admin rights and a sign-in, so the owner installs it (G-12 A).

## Context to read (only these)
- `docs/guides/local-development.md` §Prerequisites

## Acceptance criteria
- [ ] AC1: Docker Desktop is installed and the engine runs.
      Verify: `docker run --rm hello-world` → prints "Hello from Docker!"

## Test requirements
Verification command only.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
