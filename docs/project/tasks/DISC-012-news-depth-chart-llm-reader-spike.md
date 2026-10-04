---
id: DISC-012
title: "Spike: LLM reader for news and depth charts (role signals) with a historical sample"
epic: EP-15 Draft assistant
phase: 1
component: research
status: todo
ready: true
size: S
autonomy: auto
gate: G-24
depends_on: [RSCH-007]
areas: [docs/research/**, packages/ingest/**]
standards: [ml, security]
assignee:
created: 2026-09-26
completed:
---
# DISC-012 — Spike: LLM reader for news and depth charts (role signals) with a historical sample

## Objective
Assess sources (team/league news, depth-chart pages, GDELT, Wayback snapshots), ToS, cost, and extraction accuracy of a grounded LLM reader (quotes + source URL + timestamp for every extracted role claim) on a hand-labelled sample.

## Context to read (only these)
- docs/project/architecture-decisions.md D-55, D-56
- docs/evaluation/reports/DRAFT-007-backtest.md

## Acceptance criteria
- [ ] AC1: Source inventory with access, ToS, cost, historical coverage
      Verify: docs/research/news-signals.md
- [ ] AC2: Extraction accuracy on >= 50 hand-labelled articles, with every claim traceable to a quote
      Verify: spike report

## Test requirements
TDD for package code; fixtures, no network in unit tests.

## Evaluation requirements
Rolling origin [R-50, R-51]; bootstrap CIs [R-54]; ship rules pre-registered before running.

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
- Claude API spend capped at US$5 for the spike (D-57).

## Follow-ups
_None._
