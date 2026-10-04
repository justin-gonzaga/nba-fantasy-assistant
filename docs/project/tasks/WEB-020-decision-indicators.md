---
id: WEB-020
title: "Decision indicators on Players: range, role change, punt fit, consistency, age, market"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [WEB-019]
areas: [apps/web/**, apps/api/**, apps/pipeline/src/fantasy_pipeline/**, packages/models/**]
standards: [frontend, design, backend]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# WEB-020 — Decision indicators

## Objective
The owner (2026-10-02): "not just healthy rank, we also need other indicators to help decision-making." Give each
player a small set of indicators that answer the auction questions (*how good, how sure, what's changing, does he
fit my build, is he a bargain*), each computed from stored evidence with a plain one-line "why" (explanations
standard: no invented facts). The row stays scannable; the detail sheet gets a **Decision panel**.

## Context to read (only these)
- `docs/standards/design-language.md` (Badge, Surface, voice), WEB-018 (badges), WEB-019 (healthy rank)
- `docs/evaluation/reports/DRAFT-002-backtest.md` § Calibration (80 % intervals cover 75–85 %)
- `apps/api/src/fantasy_api/players.py`, `apps/pipeline/src/fantasy_pipeline/draft_values.py`

## Indicators (evidence first)
| Indicator | Question | Computed from | Shown as | Why line example |
|---|---|---|---|---|
| **Healthy rank** (WEB-019) | How good if he plays? | values at 72 games | "Healthy #17" | "#118 after expected missed games (45 of 82); #17 at 72" |
| **Range** | How sure is the projection? | stored per-stat `sd` (calibrated 80 % intervals, DRAFT-002) | 80 % range for PTS/REB/AST + games; a **Certainty** label (high/medium/low = tercile of the games + mpg interval width) | "80 % range: 21–29 pts, 52–74 games" |
| **Role change** | Is his role growing or shrinking? | projected mpg vs last season's mpg; M1 features (team change, vacated minutes) | "Bigger role +4.1 min" / "Smaller role" when \|Δ\| ≥ 3 | "Projected 31.2 min vs 27.1 last season; 1,240 team minutes left" |
| **Punt fit** | Does he suit my strategy? | rank under the selected punt vs under all categories | "Fits punt AST" when he gains ≥ 20 places | "#64 overall, #31 when punting AST" |
| **Category profile** | Where does his value come from? | stored `s_<cat>` strengths | 9 mini bars (detail; desktop rows) | "Strong: BLK, REB, FG%; weak: FT%" |
| **Consistency** | Will he swing weeks (H2H)? | last season's week-to-week sd of his 9-cat value (weekly table) | "Steady" / "Volatile" (terciles of players with ≥ 15 weeks) | "Weekly value varied ±1.8 (pool median ±1.1)" |
| **Age** | Rising or declining? | age at mid-season + the aging curve sign (D-52) | "Age 31 · aging −2 %" | "Aging curve takes 2 % off his rates" |
| **Market** (needs DATA-034) | Is he a bargain? | Yahoo average auction cost (pre-draft) vs our $ | "Bargain +$8" / "Pricey −$6" when \|Δ\| ≥ $5 | "Yahoo drafters pay $22; we value him at $30" |

Sort options gain: Healthy rank, Certainty, Role change, Bargain (when market data exists). Filters gain: Certainty
(high only), Bigger role, Bargain.

## User stories and edge cases
| Persona / situation | Story | Edge cases |
|---|---|---|
| Owner mid-auction, phone | "Is $25 too much for him?" | the row shows $ + at most one signal chip (priority: Injured today > Bargain/Pricey > Bigger/Smaller role > Fits punt > Volatile); everything else in the sheet |
| Owner planning a punt build | "Who fits punt FT%?" | Punt fit computed against the selected strategy; hidden under "All categories" |
| Owner comparing two similar players | "Which is the safer pick?" | Certainty and Consistency side by side in the sheet (Compare view is a follow-up) |
| Rookie / no last season | | Role change and Consistency absent (no history), stated as "No NBA history" in the sheet |
| Market data not imported | | Market rows hidden, sort/filter options hidden; no error |
| Screen reader | | each indicator reads as words; bars have text values |
| Pre-season vs in-season | after tip-off, ranges come from the in-season model when it ships | the panel labels which projection it uses |

## Acceptance criteria
- [x] AC1: the pipeline publishes per player: stat `sd`s (already stored), projected and last-season mpg with the
      M1 role drivers, weekly consistency (sd + percentile), age and aging factor; values include per-variant ranks
      for the punt-fit comparison.
      Verify: `uv run pytest -q apps/pipeline/tests/test_draft_publish.py -k "age or consistency or swing or role_context"`
- [x] AC2: `/players` returns `indicators` per player (healthy, range, role, puntFit, consistency, age, market?)
      with values and a `why` string built only from those values; absent inputs → absent indicator.
      Verify: `apps/api/tests/test_players.py::test_indicators_*` (one per indicator + missing inputs + why strings
      contain only served numbers)
- [x] AC3: Players rows show ≤ 1 signal chip by priority; the detail sheet has a Decision panel with every available
      indicator and its why; the new sorts and filters work.
      Verify: `PlayersPage.test.tsx` (chip priority, panel, sorts, filters, missing-data cases)
- [x] AC4: the thresholds (Δmpg 3, punt gain 20 places, market $5, terciles) are named constants in one module with
      a test pinning them, so changing one is a reviewed decision.
      Verify: `apps/api/tests/test_indicators.py::test_thresholds_are_pinned`
- [x] AC5: design-language checklist §7 met (tokens, Badge, both themes, 44 px, reduced motion).
      Verify: `design.test.ts`; reviewer §7 pass

## Test requirements
TDD: indicator functions are pure (inputs → value + why); seeded parquet for the API; page fixtures.

## Evaluation requirements
n/a for presentation. Range relies on the calibration measured in DRAFT-002 (80 % coverage 75–85 %); if the in-season
model replaces it, its own calibration applies. Market is a comparison, not a model.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/pipeline/tests/test_draft_publish.py::test_history_carries_age, ::test_consistency_measures_week_to_week_swings, ::test_a_steadier_player_has_a_lower_weekly_sd, ::test_relative_swing_is_sd_over_level_for_positive_contributors, ::test_role_context_carries_the_minutes_models_drivers (sds were already published with the projection) | pass |
| AC2 | test | apps/api/tests/test_indicators.py (15, incl. role drivers in the why line; range, certainty incl. draft-pool cut points, role, punt fit, consistency, age, missing inputs, signal priority); test_players.py::test_indicators_are_served_with_a_row_signal, ::test_indicators_absent_without_inputs | pass |
| AC3 | test | PlayersPage.test.tsx › "decision indicators (WEB-020 AC3)" + "one row priority for badges and signals" (combined 2-chip cap, At a glance panel, sorts, signal filter in URL, hidden without data) | pass (217 web tests) |
| AC4 | test | test_indicators.py::test_thresholds_are_pinned | pass |
| AC5 | test | design.test.ts (tokens only, no raw colours); icon + word chips via the Badge primitive | pass |

## Implementation history
- 2026-10-02 — Specified from the owner's request.
- 2026-10-03 — Built TDD (pipeline: age + consistency files; API: `indicators.py`; web: signal chip, At a glance
  panel, sorts, signal filters, demo data). **Real-data check before shipping** caught two calibration problems:
  certainty thirds over the whole pool made 135/150 top players "High certainty" (incl. Giannis, 26–64 games) →
  cut points from the expected draft pool; absolute weekly swings made 93/150 stars "Volatile" → swings relative to
  the player's own weekly level. After: High 73 / Medium 43 / Low 34; Volatile 20; Giannis and Embiid Low certainty.
  Market (DATA-034) remains a follow-up.

## Decisions
- Review (FAIL → fixed): role drivers published (`role_context.parquet`: team change, team minutes freed up; the M1
  features) and named in the why line; AC1's Verify line now points at the real tests; one priority for the row
  (WEB-018 badges first, then the WEB-020 signal; at most 2 chips + "+N"), which reconciles the two specs.
- Scoped out (deviation from the table's example): the aging-curve percentage in the Age why line — the per-player
  aging factor isn't published; Age shows the age only.
- Certainty cut points from the draft pool; consistency = sd / mean weekly value for positive contributors
  (percentile over all of them). Filters are any-of (like the badge filter).
- One signal chip per row (not a wall of icons): the design language's clarity rule; everything is in the sheet.

## Known issues
_None._

## Follow-ups
- DATA-034 Yahoo market values (average auction cost) for the Market indicator.
- WEB-021 Compare two or three players side by side.
- RSCH-008 Q3 may add a "Playoff schedule" indicator if it passes.
