# Project Specification — NBA Fantasy Decision Assistant

Version 0.1 (planning baseline, 2026-09-24) · Owner: project owner (human) · Status: **Approved** (G-00, 2026-09-24).

## 1. Purpose

A personal decision-support system for one Yahoo NBA Fantasy league. It ingests NBA and Yahoo data,
keeps a reproducible analytical data platform, produces calibrated projections and simulations, and turns
them into **explained, auditable recommendations**: lineups, adds and drops, streaming, trades, and matchup
strategy. Every recommendation is logged and scored against what actually happened.

The product is **better decisions per minute of attention**. ML is a means, not a goal.

## 2. Users and usage

- **Single user** (the owner), mostly on a phone, both through the dashboard and through Claude Code Remote Control.
- Typical interactions:
  - "What's my lineup today?"
  - "Who should I stream this week?"
  - "Is this trade good?"
  - "How am I tracking against my opponent?"
  - "Were last week's recommendations any good?"

## 3. Goals

| ID | Goal |
|---|---|
| G1 | Reliable, idempotent ingestion of NBA and Yahoo data with **point-in-time (as-of) history** |
| G2 | Layered data platform (raw → staging → core → marts → features) with tests and lineage |
| G3 | Player projections as **distributions** (mean and uncertainty) per fantasy category, plus availability probability |
| G4 | Decision engine for lineup optimisation, matchup and season simulation, waiver/streaming/drop ranking, and trade evaluation. It is driven by league settings and supports **every Yahoo NBA scoring format**: H2H Categories, H2H One Win, H2H Points, Rotisserie, and Points. |
| G5 | Every recommendation carries structured evidence and a plain-language explanation |
| G6 | Evaluation framework: walk-forward backtests, historical replay without leakage, and recommendation-outcome tracking against baselines |
| G7 | Mobile-friendly dashboard focused on decisions |
| G8 | Reproducible local → CI → production path, operable remotely |
| G9 | A repository that lets Claude Code agents develop it autonomously with little supervision |

## 4. Non-goals (v1)

- Supporting more than one league or user, or multi-tenancy
  - _Revised 2026-09-24 (D-31): the design must allow a **small number of other users** (each with their own Yahoo account and league) without re-architecture. Scaling to a large user base remains a non-goal._
- Automatically executing Yahoo roster moves. v1 is read-only; write access is a later gate.
- DFS, betting, or any monetisation (Yahoo ToU forbids it)
- Real-time, sub-minute updates during games
- Deep learning or LLM-generated facts. LLMs may only rephrase evidence that has already been computed.
- Enterprise infrastructure (Kubernetes, Spark, a hosted warehouse)

## 5. Functional requirements

### 5.1 Data acquisition
- FR-D1: Snapshot the Yahoo league at least daily: settings, teams, rosters, matchups, scoreboard, transactions, free agents/waivers (top-N by rank plus all rostered), and player ownership percentages.
- FR-D2: Ingest the NBA schedule, completed box scores, player and team reference data, and historical game logs for at least 3 prior seasons.
- FR-D3: Ingest official injury reports several times per game day and keep every version.
- FR-D4: Store every raw payload immutably with `observed_at` (the time we saw it), source, request parameters, and a content hash.
- FR-D5: Maintain an NBA ↔ Yahoo player-ID crosswalk with a manual override file.
- FR-D6: Support backfills for any date range, and incremental runs. All jobs are idempotent.

### 5.2 Scoring-format support (all Yahoo NBA formats)
- FR-S1: Support every Yahoo NBA scoring format through one configuration read from league settings:

  | Format | Objective the engine maximises |
  |---|---|
  | **H2H Categories** | E[category wins − losses] this week (ties per league rule) |
  | **H2H One Win** | P(win the matchup), where a matchup is won by winning more categories than the opponent. This is a different objective from H2H Categories: it favours punting and concentrating on contested categories. |
  | **H2H Points** | P(my fantasy points > opponent's) this week (E[points] as a secondary figure). Points = Σ stat × league stat modifier. |
  | **Rotisserie** | E[season standings points] across all categories vs all teams, with season-long games/innings caps |
  | **Points (season total)** | E[season fantasy points] subject to games-played limits |

- FR-S2: Support any category set Yahoo allows. This includes:
  - 8-, 9-, 10- and 11-category leagues
  - ratio categories: FG%, FT%, 3P%, A/TO, and any makes/attempts or A/TO ratio
  - counting categories: DD, TD, and turnovers as a negative category
  - custom stat modifiers for points leagues
- FR-S3: Support the league's roster and transaction rules:
  - roster slot configuration, including IL, IL+ and NA slots
  - lineup lock cadence (daily-today, daily-tomorrow, weekly)
  - weekly and season acquisition limits
  - waiver type (rolling priority, FAAB, continuous)
  - minimum and maximum games-played limits
  - playoff weeks, and the tie-break rules
- FR-S4: Every format is covered by golden tests, using a recorded Yahoo settings fixture for each format. Where we cannot obtain a fixture, a synthetic one is built from the documented Yahoo settings schema.

### 5.3 Analytics and intelligence
- FR-A1: Compute league-aware category metrics. Percentage categories are volume-weighted, and turnovers are negative.
- FR-A2: Produce per-player, per-game projections for each scoring category, with uncertainty, as of a decision timestamp.
- FR-A2b: **Cold start**: players with little NBA history (rookies, G League call-ups, international signings) get projections from league-translated pre-NBA stats (G League, NCAA, EuroLeague/EuroCup) + draft/age/position priors, blended with NBA data via empirical Bayes (D-40/D-41).
- FR-A3: Estimate P(plays) per player and game from injury designation and context.
- FR-A4: Compute schedule opportunity: games remaining, off-night games, back-to-backs, and lineup-slot contention.
- FR-A5: Simulate a weekly matchup, or the season for roto and points formats, to get:
  - P(win) per category
  - expected category wins
  - P(win matchup)
  - the points distribution

  Which of these are reported depends on the format.
- FR-A6: The methods for ML and statistical components must be grounded in established theory and peer-reviewed or citable literature (see `docs/research/ml-literature-review.md`). Each model card cites its sources and explains any deviation from them.

### 5.4 Decisions
- FR-R1: Daily lineup. Choose the optimal active lineup under position eligibility, maximising expected matchup value.
- FR-R2: Add, drop, and stream candidates, ranked by marginal matchup value (this week) and marginal rest-of-season value.
- FR-R3: Trade evaluation. Show the change in expected category wins for the rest of the season and the playoff weeks, for both sides.
- FR-R4: Opponent analysis. Show the opponent's projected categories, their weaknesses, and contested categories where punting or targeting is possible.
- FR-R5: Each recommendation includes:
  - the alternatives considered
  - the expected value delta
  - a confidence level
  - evidence (facts, derived metrics, predictions)
  - an explanation
- FR-R6: Log every recommendation, with its inputs and model versions, so it can be reproduced and scored.

### 5.5 Evaluation
- FR-E1: Walk-forward backtest of projections against baselines, with confidence intervals.
- FR-E2: Historical replay that runs the decision engine at past timestamps, using only data observed before them.
- FR-E3: Score recommendation outcomes: recommended vs. actual vs. baseline decisions, using realised stats.
- FR-E4: Calibration reports for probabilities (availability, category wins).

### 5.6 Dashboard
- FR-UI1 to FR-UI6:
  - Today (lineup and alerts)
  - This week (matchup)
  - Waivers and streaming
  - Player explorer
  - Trade analyser
  - System (data freshness, model and recommendation performance)
- FR-UI8: **Player profiles** (D-48): form and game log, forecast with ranges, context and risks, and a fantasy verdict for the owner's league, plus a daily LLM-written summary grounded only in our data (every number verified against a tool result).
- FR-UI7: Natural-language questions ("who should I stream for blocks?", "compare X vs Y") in the dashboard and via the Telegram bot. An LLM answers by calling vetted analysis functions, and every number comes from a tool result (D-36).

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR1 Cost | Recurring spend ≤ **US$10/month** (target $0–6) without approval |
| NFR2 Freshness | Daily lineup recommendations available ≥ 60 min before the first tip-off of the (US/Eastern) game day |
| NFR3 Reproducibility | Clean machine → running system with documented commands; any past recommendation reproducible from stored snapshots and a git SHA |
| NFR4 Correctness | No temporal leakage in features, evaluation, or replay; enforced by tests |
| NFR5 Security | No secrets in git; least-privilege Yahoo scope; dashboard not publicly reachable without auth |
| NFR6 Operability | Health, freshness and failure status visible in the dashboard and via `just status`; failures alert the owner |
| NFR7 Maintainability | Typed and tested; component boundaries enforced by import contracts; ADRs for significant decisions |
| NFR8 Agent-operability | Each task completable by one Claude session with explicit acceptance criteria and automated checks |
| NFR10 Awake-window operation | User-facing processing and notifications run only inside the owner's configurable awake window (default 07:00–23:00 Australia/Sydney). Overnight changes are consolidated into one morning catch-up. The evening digest flags games that lock before the owner wakes (weekend/early US games), so those are set the night before. Overnight capture is limited to data that can't be recovered later. Official injury reports are archived by the NBA, so they can be backfilled rather than polled overnight. |
| NFR9 Performance | Dashboard p95 < 1 s for cached views; a full daily pipeline < 15 min on the dev laptop |

## 7. Constraints

- Claude **Pro** subscription, so development must be token-efficient (see `docs/agents/agent-architecture.md` §8).
- The dev machine is Windows 11. Tooling must be cross-platform, and CI/production run on Linux.
- stats.nba.com is unreachable from cloud IPs. Historical NBA backfills run from a residential IP.
- Yahoo ToU: non-commercial use, and a 24 h retention clause for "user data" (G-04).
- Season calendar: tip-off 2026-10-20. Snapshot collection should be live by then.

## 8. Principles

1. **Decision value over model sophistication.** Every model must beat a simple baseline, measured out-of-sample.
2. **Point-in-time correctness everywhere.** Everything is keyed by when it was known, not only when it happened.
3. **Separate facts, derived metrics, predictions, optimisation outputs, rules, recommendations, and explanations** as distinct, typed artefacts.
4. **Simplest thing that preserves options.** Keep interfaces stable and implementations swappable (ADR-0003).
5. **Deterministic where possible.** Use scripts, not agents, for anything repeatable.
6. **The repository is the memory.** Project state lives in `docs/project/`, not in conversations.

## 9. Success criteria

| Horizon | Criterion |
|---|---|
| Before tip-off (2026-10-20) | Daily Yahoo and injury snapshots running and landing raw data. Planning baseline approved. |
| Phase 3 | Baseline daily lineup and streaming report (CLI or markdown) in actual use |
| Phase 5 | Replay shows the recommended lineups beat baseline B1 (below) on realised category value in ≥ 55 % of team-days, with a 95 % CI excluding 0 on mean delta |
| Phase 6 | ML projections beat the best statistical baseline on walk-forward MAE for ≥ ⅔ of the league's scored stats (paired bootstrap CI excludes 0), and availability probabilities are calibrated (ECE < 0.05) |
| Season end | Recommendation log with outcome scores. Owner rates the tool as useful. Matchup win-rate is tracked (not a success gate — too noisy). |

**Baseline B1**: the lineup the owner actually set when that data exists, otherwise "start all active players by Yahoo rank".

## 10. Glossary

- **as-of / observed_at**: the timestamp at which the system knew a fact.
- **game date**: the NBA calendar date in US/Eastern.
- **decision time**: the timestamp a recommendation is computed for.
- **category value**: the contribution to a fantasy category. Percentages are computed from makes and attempts.
- **Streaming**: short-term add/drop to use a player's games in the current matchup.
