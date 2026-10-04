---
id: DISC-009
title: "Spike: MySportsFeeds personal plan evaluation (coverage, delay, cost)"
epic: EP-01 Discovery
phase: 0
component: ingest
status: todo
ready: true
size: S
autonomy: gated
gate: G-08
depends_on: []
areas: [docs/research/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DISC-009 — Spike: MySportsFeeds personal plan evaluation

## Objective
Find out whether the ~$5/mo personal MySportsFeeds plan gives useful injuries and expected/actual lineups, how delayed "non-live" is, and whether it beats our free sources.

## Context to read (only these)
- `docs/research/2026-09-initial-research.md` §2b

## Acceptance criteria
- [ ] AC1: The owner signs up for the free trial (human action). Claude uses it to confirm exactly which NBA feeds and add-ons the personal plan includes, and the total monthly price.
- [ ] AC2: The "non-live" delay is measured for the injury and lineup feeds on at least 2 game days, compared against the official injury report and actual starters.
- [ ] AC3: Its data quality is compared with cdn.nba.com box scores for 20 games (field-level match rate).
- [ ] AC4: A recommendation is written into D-12/D-32 and the research doc: adopt, use as fallback, or reject.

## Test requirements
Spike: record results in `docs/research/nba-data.md`.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
- Requires the owner to sign up for the trial.

## Follow-ups
_None._
