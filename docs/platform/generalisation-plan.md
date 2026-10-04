# Generalisation plan: from one fantasy app to a repeatable decision-intelligence factory

Status: **Accepted** (D-58, owner 2026-09-27: kernel in this repo, Sydney housing proof, extraction starts now). Written 2026-09-27. Extends D-46, which covers only the working harness, to the whole pipeline → model → decision → frontend stack.

## 1. What the owner is asking for

1. **A repeatable way to build decision products**, not a one-off app. The NBA assistant is the first instance of a general pattern: collect data with history → clean and model it → predict with calibrated uncertainty → turn predictions into explained decisions → show them in an app. The same pattern would drive a Sydney housing intelligence platform or banking/retail insights.
2. **Claude is the builder.** The reusable parts should be shaped for how Claude works best, not for a human team: explicit contracts, scripts that check things mechanically, small well-named files, and tests as guardrails.
3. **A learning loop.** Record what worked, what didn't and why, with evidence, and distil it into a playbook. Each new product then starts from the best-known approach.
4. **A commercial path.** Either the factory itself or the products it builds should become sellable.
5. **In parallel.** None of this may slow the draft (18 Oct) or the season.

## 2. Three layers

```
┌──────────────────────────────────────────────────────────────┐
│ DOMAIN PACK (per product)  e.g. nba-fantasy, sydney-housing  │
│ sources · entities · targets · objective · decisions · screens│
├──────────────────────────────────────────────────────────────┤
│ PLATFORM KERNEL (reusable code + infra)                       │
│ ingest (write-once snapshots, paced client) · AsOfReader/Clock│
│ dbt skeleton (staging→intermediate→marts, reconciliation tests)│
│ eval harness (rolling origin, paired bootstrap, pre-registered│
│ gates) · baselines · shrinkage/ridge/logistic building blocks  │
│ decision + explanation contracts · API + web shell · Terraform │
├──────────────────────────────────────────────────────────────┤
│ HARNESS (how Claude works; D-46)                              │
│ CLAUDE.md · tasks.py + task standard · gates · decision menus │
│ skills + reviewer/researcher agents · CI + ruleset · standards│
│ lessons ledger + playbook (new)                               │
└──────────────────────────────────────────────────────────────┘
```

Rule: **domain → platform → harness**. Each layer may use the layers below it, never above. Code enforces it with import-linter, as it already does for the package layering.

## 3. Inventory: what we have, by layer

| Asset | Layer | Notes |
|---|---|---|
| CLAUDE.md skeleton, tasks.py, task standard, gates, decision menus, skills, agents, standards, DoD | Harness | Listed in harness-manifest.yaml (D-46) |
| CI workflow + main ruleset + per-PR dbt datasets + cleanup job | Harness | Generic apart from project ids |
| Commercial view, CV tracker, paper tracker | Harness (pattern) | |
| `SnapshotStore` (write-once, sidecars), `PacedClient` | Platform | Already source-agnostic |
| `Clock`, settings, logging, errors | Platform | `gamedate.py` is domain |
| Terraform bootstrap + `modules/env` (projects, WIF, SAs, buckets, datasets, retention, tests) | Platform | Parameterise the prefix and region |
| dbt project layout, `generate_schema_name`, external-table raw pattern, reconciliation tests | Platform | Model SQL itself is domain |
| Rolling-origin backtest, paired and stratified bootstrap, gate/challenger, selection vs holdout folds | Platform | Currently inside `preseason_backtest.py`; needs extracting |
| Empirical-Bayes shrinkage, ridge, logistic with class weights + prior correction, reliability tables | Platform (methods library) | Written as NBA functions; the maths is generic |
| Overrides file (owner-reviewed caps) | Platform (pattern) | "Human-reviewed adjustments with a source and date" |
| Draft board page + live helper, JS/Python parity test | Domain (pattern reusable) | The "live decision board" pattern generalises |
| `league.py`, `ScoringObjective`, valuation (G-score, VOR, $) | Domain | The *interface* `ScoringObjective` is the generic idea: every domain has an objective |
| NBA / Yahoo ingesters, all staging SQL, projections, breakouts | Domain | |
| Web prototype look, action card + why, freshness badge | Platform (UI kit) | Screens are domain |

About **60 % of what exists is reusable**, most of it already written in a domain-neutral way. The main job is moving it, not rewriting it.

## 4. Designed for Claude as the builder

- **A domain spec file.** `domain.yaml` declares the sources (URL, cadence, terms verdict), entities and grain, the time semantics (event time vs knowledge time), targets, the objective, the decisions and the screens. Claude generates the domain pack's skeleton from it, and a check keeps the code honest to it.
- **Contracts over conventions.** Typed interfaces (`Source`, `AsOfReader`, `Baseline`, `Model`, `ScoringObjective`, `Decision`, `Explanation`) with tests that any implementation must pass. Claude writes an implementation and the contract tests say whether it's right.
- **Scripts, not judgement, for anything repeatable:** task selection, validation, eval gates, cost checks, and `just new-domain`.
- **Evidence gates stay mandatory:** baselines first, pre-registered rules, a holdout split. They're the strongest defence against Claude fooling itself.
- **Small files and an index doc**, so each session reads only what the task needs.

## 5. The learning system

- **`docs/platform/lessons.md`**: an append-only ledger with one row per lesson (date · area · what we tried · outcome · evidence · lesson · layer · confidence). Seeded today from this project.
- **Capture:** a "lessons" line becomes part of each task's close-out (the `/work-task` step 8), and a monthly `/retro` promotes repeated lessons.
- **Distil:** `docs/platform/playbook.md` holds the current best way to build each layer (e.g. "minutes/opportunity dominates rate error: model exposure separately"). It's rewritten from the ledger, never from memory.
- **Measure the factory itself:** sessions and cost to first backtest, defects caught by CI, gates passed or failed. These become the commercial proof points.

## 6. Proving it: a second domain

A generalisation claim only counts once a second domain runs on the kernel without changes. Candidate: **Sydney housing** (public NSW Valuer General bulk sales, ABS, planning data):

| Kernel piece | NBA | Sydney housing |
|---|---|---|
| Snapshots | stats.nba.com JSON | weekly VG sales files |
| As-of | game date, injury report time | contract date vs settlement date vs publication date |
| Baseline | last season / Marcel | last sale × suburb index |
| Shrinkage | per-minute rates | suburb medians with few sales |
| Exposure model | minutes | days on market / sales volume |
| Objective | 9-cat value, $ | expected return / yield vs budget |
| Decision board | auction draft helper | watchlist: under-valued listings, with the why |

Success metric (pre-registered): ingestion → dbt → a baseline backtest in **≤ 5 Claude sessions with zero edits to kernel code**; any edit needed becomes a kernel fix.

## 7. Phased plan, in parallel with the NBA work

| Phase | When | What | Effort |
|---|---|---|---|
| G0 | now, alongside draft prep | This plan; lessons ledger seeded; layer tags added to harness-manifest.yaml (rename to `platform-manifest.yaml` with harness/platform/domain sections); a lesson line in the task close-out | ~1 session |
| G1 | after the draft (late Oct–Nov) | Extract the kernel inside this repo: `packages/platform-*` (ingest, asof, eval, methods, decision contracts); NBA code imports them; import-linter enforces the layers. No behaviour change: all tests and backtests reproduce | 4–6 sessions |
| G2 | Nov–Dec | Copier template + Claude Code plugin (HARN-002/003), plus `domain.yaml` and `just new-domain`; the Terraform module takes a prefix | 3–5 sessions |
| G3 | Dec–Jan | Proof: stamp the second domain, run to a baseline backtest; record the metrics | 5 sessions (the test) |
| G4 | after G3 | Commercial choice with evidence: sell domain products, offer the factory as a build service, or open-source the kernel for credibility. Update commercial-view.md | decision |

NBA work keeps priority whenever the two compete (draft week, in-season daily runs).

## 8. Decisions for the owner (D-58)

1. **Where the kernel lives:** (a) ★ packages inside this repo first, then extract once G3 proves them; (b) a separate platform repo now; (c) the template only, no shared code.
2. **The proof domain:** (a) ★ Sydney housing (public data, clear decisions, local, commercially plausible); (b) banking/retail (realistic data is private; synthetic only); (c) another sports league (easiest, but proves little).
3. **Timing:** (a) ★ G0 now, G1 after the draft; (b) everything after the season; (c) start G1 now.

## 9. Commercial note (honest)

The durable asset is probably **the factory**: a proven, Claude-operated way to go from raw public data to explained, backtested decisions in weeks. A single fantasy app is a small market and depends on Yahoo's terms. Evidence to collect along the way: time to a first backtest per domain, the cost per run, and how accurate the decisions are against baselines.
