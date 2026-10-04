---
id: DISC-008
title: "Spike: pre-game news extraction feasibility (sources, ToS, accuracy, cost)"
epic: EP-01 Discovery
phase: 0
component: ingest
status: todo
ready: true
size: M
autonomy: auto
gate: G-17
depends_on: []
areas: [docs/research/**, spike code (not merged)]
standards: [data-engineering, security, ml]
assignee:
created: 2026-09-24
completed:
---
# DISC-008 — Spike: pre-game news extraction feasibility

## Objective
Test whether D-32 option A is practical: permitted sources, extraction accuracy, latency vs the official injury report, and cost.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-32
- `docs/research/2026-09-initial-research.md` §2a

## Acceptance criteria
- [x] AC1: A candidate source list, each with its ToS/robots position on automated access (URL + date). Sources that forbid automated access are excluded.
      Verify: docs/research/news-extraction.md §1-2
- [ ] AC2: On about 3 game days, the permitted sources are fetched at T-90 and T-45 minutes for about 20 relevant players. Labels come without owner work: (a) outcome labels from the next day's box scores (played or not, started or not, minutes vs the player's recent average, so a reported minutes restriction is checkable) and (b) text labels from an independent second pass by a different, stronger model with mandatory quotes; the two model passes' disagreements are resolved by rule and reported. (Owner decision 2026-09-27: no hand-labelling.)
      Verify: docs/research/news-extraction.md §labelled sample (counts per label source)
- [ ] AC3: LLM extraction (Claude Haiku via the API, with a structured-output schema and a mandatory source quote) scored against both label sets (outcome labels are the independent ground truth; model labels measure extraction fidelity) (precision/recall per field). Hallucinated fields counted separately.
- [ ] AC4: Latency comparison: how often the news preceded the next official injury-report version, and by how many minutes.
- [ ] AC5: Measured token usage and monthly cost projection. Recommendation (A/B/C/D) written into D-32 with the evidence.

## Test requirements
Spike: record results in `docs/research/news-extraction.md`. No code is merged.

## Evaluation requirements
Extraction precision/recall with 95 % bootstrap CIs [R-54].

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
- 2026-09-27: AC1 done by the researcher subagent: 16 sources checked. Permitted: the official injury PDF, RotoWire RSS, GDELT; conditional: CBS RSS (its own ToU still unread), Bluesky. Excluded: NBA.com news and team sites, Yahoo Sports, RotoWire site, The Athletic, Underdog (site and X), Google News RSS. AC2-AC5 need real game days (season from 20 Oct), about 50 owner-labelled items and a small API spend (owner approval).

## Decisions
_None yet._

## Known issues
- AC2 needs about 30 minutes of the owner's time for labelling.

## Follow-ups
_None._
