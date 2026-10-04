# Human Approval Gates

Version 0.1 · 2026-09-24. **This is the one document to review from your phone.**

- **How to answer**: `approve G-05 A`, `approve G-06 A,B`, `reject G-09`, or `discuss G-04`. You can also say `approve all recommended except G-07`. Claude runs `/gate`, which updates this file, the linked ADRs, and the tasks.
- **Status values**: `PENDING` → `APPROVED (option)` / `REJECTED` / `DEFERRED`. Tasks linked to a gate cannot start until it is APPROVED.
- **⏰ Time-critical** items affect whether data collection can start before tip-off on **20 Oct 2026**.

## Summary

| Gate | Decision | Recommendation | ⏰ | Status |
|---|---|---|---|---|
| G-00 | Approve the planning baseline (spec, architecture, roadmap, backlog) | Approve | ⏰ | APPROVED |
| G-01 | GitHub repo & protection model | Private repo on GitHub Free | ⏰ | APPROVED (C, public) |
| G-02 | Which league, and confirm its format | You tell us the league; Claude reads the settings | ⏰ | APPROVED |
| G-03 | Yahoo developer app & API scope | Read-only scope; you register the app | ⏰ | APPROVED (A) |
| G-04 | Yahoo data retention | Keep snapshots (personal use) + a purge switch | ⏰ | APPROVED (A2) |
| G-05 | NBA data sources | Free unofficial endpoints; paid fallback only if they break | ⏰ | APPROVED (A) |
| G-06 | Where it runs | Local now; ~$5/mo VPS at Phase 8 | | APPROVED (B) |
| G-07 | Dashboard technology | React SPA (Phase 7), markdown reports before that | | APPROVED |
| G-08 | Monthly cost ceiling | ≤ US$10/mo without asking | | APPROVED |
| G-09 | LLM-written explanations | Off (templated explanations) | | APPROVED |
| G-10 | Engineering standards selections | See `standards-decisions.md` (31 items) | ⏰ | APPROVED |
| G-11 | Agent autonomy & merge tiers | Tier A auto / B review / C gated | ⏰ | APPROVED |
| G-12 | Installing dev tools on your laptop | Claude installs via winget/uv; you do Docker Desktop | ⏰ | APPROVED |
| G-13 | Time zone & daily schedule | Australia/Sydney display; runs keyed to US/Eastern | | APPROVED (A) |
| G-14 | ML & decision methodology | Decomposed probabilistic projections + format objectives | | APPROVED |
| G-15 | Fast-track the snapshot collector before tip-off | Approve | ⏰ | APPROVED (A) |
| G-16 | Dashboard access / security model | Tailscale only; no public URL | | APPROVED |
| G-25 | Users, profiles & settings: store, roles/invites, first slice (D-64) | Firestore · invites + owner/member roles · identity + settings first | | APPROVED (A + BQ copy, A, A) |
| G-26 | Missed games: value at replacement level instead of zero (D-65) | A, replacement fill + IL replay | ⏰ draft 18 Oct | APPROVED (A) |
| G-27 | Monitoring: how alerts reach you (D-66) + budget alert on the billing account | A watchdog job | | APPROVED (A) |
| G-28 | Draft simulator: surface, opponent model, pace (D-67) | A web page · A calibrated styles · A real timers + fast-forward | ⏰ draft 18 Oct | APPROVED (A, A, A) |
| G-29 | ML plan amendment: team/coach context in projections (EXP-004) | Asked only if ANL-010 says go | | NOT NEEDED (ANL-010 NO-GO) |
| G-30 | Telegram linking transport + how the daily job reads user settings (D-68) | A webhook · A shared users package | | APPROVED (A, A) |
| G-31 | Season replay: data delivery, lineups, rivals, waivers, seasons (D-69) | A · A · A · A · A | | APPROVED (A, A, A, A, A) |
| G-32 | ML plan amendment: games for players returning after a lost season (DRAFT-022) | Approve the pre-registration | ⏰ | APPROVED |
| G-33 | Where league-specific values are computed, and scale targets and spend (D-70, D-71) | B server on demand with cache · confirm SLOs, no min instance yet | | APPROVED (B; A, A, A) |
| G-34 | Accounts and leagues: who may register, sign-in, pictures, scope, phone nav (D-72) | Open sign-up behind a flag, reviewed first · Google + email/password · uploads with report/hide · shell scope · no seventh tab | | APPROVED (all ★) |
| G-36 | Going public: what to do about the owner's email in git history, and the licence (SEC-001) | A fresh-snapshot public repo ★ · B rewrite history · C accept · licence | ⏰ (free CI) | APPROVED |
| G-35 | Sign-in methods, user-data ruleset, spend, rename (D-73, D-74) | Google + email/password · phone built but off · Identity Platform in dev · SDK token storage + CSP · age 16+ (US, AU) | | APPROVED (all ★; 16+) |
| G-21 | Approve the ML plan, draft slice (preseason projections + auction $ valuation + live auction helper) | Panels by ~27 Sep | ⏰ draft 18 Oct | APPROVED |
| G-22 | Approve the data design, draft slice (NBA history + schedule + league settings → player pool → projections) | Panels by ~27 Sep | ⏰ | APPROVED |
| G-20 | Approve the data pipeline design (sources → raw → staging → intermediate → marts → features → models) | Review via panels once all raw sources are confirmed | ⏰ | PENDING |
| G-19 | Approve the ML methodology plan (verified literature, per-component design) | Review via panels after RSCH-001 + RSCH-004 | ⏰ (draft projections depend on it) | APPROVED |
| G-18 | iOS app phase: macOS build route (cloud macOS runners vs a Mac) + Apple Developer fee (US$99/yr) | Decide when the iOS phase starts | | PENDING |
| G-17 | Architecture & technology selections (D-01…D-35) | See `architecture-decisions.md`; ⏰ subset first | ⏰ | APPROVED |

---

## G-00 · Approve the planning baseline
**Status**: APPROVED — 2026-09-24 (reconciled baseline approved via review panels; review answers: cloud from day one, read-only prod logs for Claude, auto model promotion)
- **Decision**: accept `project-spec.md` (goals, scope, requirements), `roadmap.md`, and the backlog structure as the working baseline.
- **Technical choices are not part of this gate.** They are decided item by item in G-17 (architecture/tech) and G-10 (standards), and the ADRs become Accepted as their D/S items are chosen.
- **Options**: A. approve · B. approve with the listed changes · C. revise first
- **Recommendation**: A.
- **If there is no answer**: nothing is implemented.
- **Blocks**: all FND and DATA tasks.

## G-01 · GitHub repository & branch protection
**Status**: APPROVED (C: **public repo**, revised 2026-09-24 for the CV showcase; publish only after the SEC-001 audit)
- **Decision**: where the code lives remotely, and how `main` is protected (standards S-21). Verified: private repos on GitHub Free have **no** branch protection or deploy reviewers.
- **Options**:
  - A. Private + Free + protection by local hooks and scripts ($0)
  - B. Private + GitHub Pro (~US$4/mo; real protection)
  - C. Public ($0; your league data and architecture become public)
- **Recommendation**: A. Move to B if an unreviewed commit ever lands on `main`.
- **Human action**: create or sign in to your GitHub account and run `gh auth login` once (after G-12). Claude creates the repo.
- **If there is no answer**: work stays local-only (git without a remote, no CI).
- **Blocks**: FND-006, FND-008.

## G-02 · League identification & format confirmation
**Status**: APPROVED — 2026-09-24: a single friends' league; no earlier seasons. DISC-002 discovers the league ID automatically
- **Decision**: which Yahoo league(s) to track. Claude then reads the scoring format, categories, roster slots, lock cadence, acquisition limits, and playoff weeks from the API. It does not guess them.
- **Your input**: the league name (or ID), and whether prior seasons of the same league exist.
- **If there is no answer**: DISC-002 lists your leagues and asks.
- **Blocks**: DISC-002.

## G-03 · Yahoo developer app & API scope
**Status**: APPROVED (A) — 2026-09-24. **Superseded 2026-09-25: the Yahoo API is closed to existing apps (ADR-0025); applying to the new programme (YAHOO-001)**
- **Decision**: API permission level.
- **Options**:
  - A. **Fantasy Sports: Read**
  - B. Read/Write (would allow automatic lineup/roster moves later)
- **Recommendation**: A. Automatic moves are a separate future decision with its own risks.
- **Human action (~10 min)**: register an app at developer.yahoo.com, select Fantasy Sports Read, put the client ID/secret in `.env` (Claude will give you exact steps in DISC-001), then run `just yahoo-login` once for consent.
- **Blocks**: DISC-001, DATA-003.

## G-04 · Yahoo data retention ⚖️
**Status**: APPROVED (A2: keep snapshots, pseudonymise other managers at ingestion, purge switch) — 2026-09-24
- **Context**: the Yahoo API Terms of Use say "user data" must be deleted within 24 h unless the docs allow indefinite storage. It is unclear whether league rosters, stats, and transactions count, and the fantasy-specific terms page was unavailable (404) on 2026-09-24. Point-in-time history is what makes honest backtesting possible (ADR-0005).
- **Options**:
  - A. Keep raw Yahoo snapshots indefinitely, locally/privately, for personal non-commercial analysis, with a one-command purge (`just purge-yahoo`) in case Yahoo objects or the terms clarify against it
  - B. Keep only derived aggregates (no raw payloads) beyond 24 h. Weakens replay.
  - C. Keep nothing beyond 24 h. Replay and waiver evaluation become impossible.
- **Option A2** (added 2026-09-24, selected): as A, but at ingestion we pseudonymise other managers (names → 'Team N', GUIDs → salted hash), drop fields we don't use, and keep the purge switch. The owner's own team stays identified.
- **Recommendation**: A, **plus DISC-007** to look for clearer fantasy-specific terms. This is a judgement call about terms of service. Claude cannot give legal advice, and the choice is yours.
- **DISC-007 update (2026-09-27, context only; the decision stands)**: the fantasy-specific API terms are still a 404. The quoted clauses are in `docs/research/yahoo-api.md` §DISC-007. The 24 h deletion clause is written for API users; under assisted import we don't call the API. The ambiguity about broader intent remains, and no Yahoo statement resolves it. No clause requires pseudonymising other managers; A2 does it by choice. Nothing requires re-opening this gate; the owner may revisit it with the quotes.
- **Blocks**: DATA-004, DATA-005 (storage behaviour).

## G-05 · NBA data sources
**Status**: APPROVED (A) — 2026-09-24
- **Options**:
  - A. Free unofficial NBA.com endpoints (cdn.nba.com + stats.nba.com from your home IP) + official injury PDFs
  - B. BALLDONTLIE paid plan (US$9.99/mo) as the primary source
  - C. A + automatically switch to B on failure
- **Recommendation**: A, with B pre-evaluated as a manual fallback (a new gate if needed). Risk: the unofficial endpoints can change without notice; contract tests detect this within a day.
- **Blocks**: DISC-003, DISC-004, DATA-006, DATA-009.

## G-06 · Deployment model
**Status**: APPROVED (B, from collection start rather than Phase 8) — 2026-09-24
- **Options**:
  - A. Local only ($0; the laptop must be on at run times)
  - B. Hybrid VPS ~US$5/mo from Phase 8
  - C. Serverless (Cloud Run)
  - D. A home mini-PC or Raspberry Pi (one-off ~US$100)
- **Recommendation**: A now; decide B vs D at Phase 8.
- **Question for you**: is the laptop usually on and awake in the morning, US/Eastern (i.e. AEST late morning/afternoon)?
- **Blocks**: PROD-003.

## G-07 · Dashboard technology
**Status**: APPROVED (A: React SPA) — 2026-09-24
- **Options** (S-24):
  - A. React SPA
  - B. Streamlit
  - C. HTMX
  - D. Evidence
- **Recommendation**: A in Phase 7. Before then, recommendations arrive as markdown reports readable on your phone.
- **Blocks**: WEB-001.

## G-08 · Recurring cost ceiling
**Status**: APPROVED (A: ≤ US$10/mo; includes GCP + Claude API usage) — 2026-09-24
- **Options**: A. ≤ US$10/mo without asking · B. $0 unless asked · C. another amount
- **Recommendation**: A. The expected spend is $0 through Phase 7, then ~$5.
- **Note**: Claude Pro is separate and not counted.

## G-09 · LLM-written explanations
**Status**: APPROVED (A: templated explanations) — 2026-09-24
- **Options**:
  - A. Off: deterministic templated explanations
  - B. On: the Claude API (Haiku) rephrases the evidence, ~US$0.10–1/mo, **billed separately from Claude Pro**, and must pass the numbers-match test
- **Recommendation**: A for now; revisit after Phase 5.

## G-10 · Engineering standards selections
**Status**: APPROVED (all S-01…S-31 selected via panels) — 2026-09-24
- **Decision**: choose options S-01 to S-31 in [`standards-decisions.md`](standards-decisions.md). Each has pros/cons and a ★ recommendation.
- **Quick answer**: `accept all recommended` or `accept recommended except S-xx B`.
- **Blocks**: STD-001, and through it all implementation tasks.

## G-11 · Agent autonomy & merge tiers
**Status**: APPROVED (A: tiered) — 2026-09-24
- **Options** (S-20):
  - A. Tier A (routine code) auto-merges when CI and the reviewer pass; Tier B (standards, architecture, CI, infra, `.claude/`) waits for your approval; Tier C (gated) waits for a gate
  - B. You approve every PR
  - C. Everything auto-merges
- **Also**: the permission mode for autonomous sessions. The recommendation is `acceptEdits` plus the hook guardrails, not `bypassPermissions`.
- **Recommendation**: A.
- **Blocks**: FND-008, FND-009.

## G-12 · Installing dev tools on your laptop
**Status**: APPROVED (A: Claude installs uv, just, gh, gcloud, Terraform; owner installs Docker Desktop + does the logins) — 2026-09-24
- **Needed**: `uv`, `just`, `gh` (GitHub CLI), Docker Desktop (for container parity), and Tailscale (Phase 7+).
- **Options**:
  - A. Claude installs uv, just, and gh via `winget`/`uv tool`; you install Docker Desktop and Tailscale (they need admin rights and sign-in)
  - B. You install everything using the guide
  - C. Skip Docker for now (S-23 B)
- **Recommendation**: A.
- **Blocks**: FND-001.

## G-13 · Time zone & daily schedule
**Status**: APPROVED (A: Australia/Sydney, awake window 07:00–23:00) — 2026-09-24
- **Assumption A-02**: you are in Australia/Sydney. Storage is UTC, and NBA game dates are US/Eastern.
- **Proposed schedule** (Sydney time, during AEDT):
  - Yahoo + NBA snapshot at 16:00 (≈ 01:00 ET, after the previous night's games finalise)
  - injury snapshots at 01:00, 05:00, 08:00, and 09:30 (≈ 10:00/14:00/17:00/18:30 ET)
  - lineup report ready by 09:00, about 1 h before most tip-offs
- **Options**: A. as proposed · B. adjust the times/time zone.
- **Recommendation**: A. Confirm your time zone.

## G-14 · ML & decision methodology (literature-grounded)
**Status**: APPROVED (A: D-16/17/18/19/20 selected via panels) — 2026-09-24
- **Decision**: approve ADR-0012 (decomposed probabilistic projections, baselines first, statistical promotion gate) and ADR-0018 (scoring formats as pluggable objectives).
- **Options**:
  - **A. Decomposed**: availability × minutes × per-minute rates, calibrated distributions, and Monte Carlo simulation feeding format-specific objectives. Empirical-Bayes baselines ship first, and ML replaces them only via the gate.
  - B. One gradient-boosted model per stat, used directly with static player rankings
  - C. A full hierarchical Bayesian model (PyMC)
- **Recommendation**: A.
- **Why this is grounded** (full entries in [`ml-literature-review.md`](../research/ml-literature-review.md)):

  | Ref | What it establishes | How it applies here |
  |---|---|---|
  | [R-11] Efron & Morris 1975; [R-12] Brown 2008 | Shrinking noisy player rates towards a group mean beats raw averages, both theoretically and empirically in-season | Our baseline projector, and the bar ML must clear. Their evidence is from baseball rates, so we test it on NBA per-minute stats |
  | [R-13] Tango's Marcel | A simple weighted-recency + regression-to-mean system is a hard-to-beat practitioner benchmark | The minimum baseline (practitioner, not peer-reviewed) |
  | [R-01] Rosenof 2023 | Z-scores ignore week-to-week variance; "G-scores" fix this for category leagues | The static valuation baseline and explanation aid |
  | [R-02] Rosenof 2024; [R-03] Rosenof 2025 | Player value in H2H and roto depends on team context and the matchup ("H-scoring") and should be optimised dynamically | Justifies simulation-based marginal value per format (ADR-0018) over static rankings |
  | [R-20] Friedman 2001; [R-21] Ke et al. 2017 | Gradient boosting is a strong, efficient learner for tabular nonlinear interactions | The minutes and availability models |
  | [R-22] Koenker & Bassett 1978 | Quantile regression estimates conditional distributions | The uncertainty of minutes |
  | [R-30] Cameron & Trivedi 2013 | The negative binomial handles over-dispersed counts | Stat-line distributions for simulation |
  | [R-41, R-42] Gneiting & Raftery 2007; Gneiting et al. 2007 | Evaluate probabilistic forecasts with proper scores, maximising sharpness subject to calibration | Our distribution metrics and gate |
  | [R-46, R-47] Zadrozny & Elkan 2002; Niculescu-Mizil & Caruana 2005 | Boosted trees give miscalibrated probabilities, and isotonic/Platt calibration fixes this | The design of the availability model |
  | [R-50, R-51] Tashman 2000; Bergmeir & Benítez 2012 | Time-ordered (rolling-origin) validation is required for temporal data | Walk-forward validation only |
  | [R-53–R-55] Diebold & Mariano 1995; Efron & Tibshirani 1993; Künsch 1989 | Paired significance tests and block bootstrap for autocorrelated errors | The promotion gate |
  | [R-60] Kaufman et al. 2012 | Leakage means using information not legitimately available at prediction time | The `AsOfReader` design and leakage tests |
  | [R-04] Hunter et al. 2016 | Integer programming for fantasy lineup construction | The lineup MILP |
  | [R-61] Glasserman 2003 | Common random numbers reduce the variance of simulated differences | The marginal-value estimates |

- **Caveats**:
  - Several references are marked "(to read)". RSCH-001 verifies them before any ML task starts.
  - There is no peer-reviewed source yet for NBA minutes models or injury-designation base rates (RSCH-002). Those parts rely on empirical validation.
- **Blocks**: ML-002, ML-003, ML-004, DEC-002–DEC-008.

## G-15 · Fast-track the snapshot collector before tip-off ⏰
**Status**: APPROVED (A) — 2026-09-24
- **Context**: Yahoo FA pools, ownership, and injury-report history cannot be recovered later. Starting collection by 20 Oct 2026 gives a full season of point-in-time data for evaluation.
- **Options**:
  - A. Fast track: build a minimal, well-tested collector path first (FND core pieces → DATA-001–DATA-008) and defer the rest of Foundation (Docker, full CI polish)
  - B. The normal sequence (collection likely starts in November)
- **Recommendation**: A.

## G-17 · Architecture & technology selections
**Status**: APPROVED (all D-items selected via panels; ARCH-001 reconciles docs) — 2026-09-24
- **Decision**: choose options D-01 to D-30 in [`architecture-decisions.md`](architecture-decisions.md). Each has a "Learn" primer, pros and cons, and a justified ★ recommendation. ML items cite the literature.
- **Quick answer**: `D: accept all recommended`, or answer the ⏰ subset first (D-01, D-04, D-05, D-07, D-12, D-13, D-14) and the rest later.
- **You can ask** `explain D-xx` or `compare D-xx A vs B` to learn more before choosing.
- **After selection**: task ARCH-001 revises the architecture docs and ADRs to match, and removes the PROPOSAL banners.
- **Blocks**: ARCH-001, and through it the implementation tasks.

## G-21 · ML plan, draft slice
**Status**: APPROVED — 2026-09-25 (panels: Q1 Marcel+EB with backtest, Q2 G-score+VOR$, Q3 full helper, Q4 backfill 2015-16+; D-49)
- Owner decision (2026-09-25): split the approvals so the draft slice comes first (the draft is Sun 18 Oct 17:00 AEDT). The same rigour applies: verified references only (ML standard §0).
- Covers: preseason season projections (Marcel/EB, aging, games played, rookies), auction $ valuation for a 16-team $200 league, and the live auction helper logic.
- **Blocks**: DRAFT-002, DRAFT-003, DRAFT-005.

## G-21b · DRAFT-002 backtest result: which projection ships (2026-09-25)
**Status**: APPROVED — 2026-09-25 (owner panels: ship the hybrid H1; gate on season-total value; judge the rank criterion on all 8 folds pooled; D-51)
- **Finding (8 rolling folds, 2018-19 … 2025-26; report docs/evaluation/reports/DRAFT-002-backtest.md)**: the gate as written picks **B0** (last season), because on *per-game* 9-cat value ranking B0 wins every fold.
- **Diagnosis** (scratch diagnostic, to be added to the report):
  - With the realised minutes, B1/C1 per-minute rates rank far better than B0's (Spearman 0.947 / 0.940 vs 0.913).
  - The gap is **minutes per game**: the flat 3-year weighted mpg is worse than last season's (MAE 4.44 vs 4.21).
  - On **season totals** (per game × games, what a season-long draft rewards), **C1 rates × last-season mpg × Marcel games** beats B0 in **8/8 folds** (mean 0.725 vs 0.712).
  - B1/C1 games projections beat B0 (MAE 14.2 vs 16.8, CI excludes 0).
  - Rookie priors beat a league-average rookie on 12/12 stats, and the 80 % intervals cover 78–84 %.
- **Options**:
  - ★A ship the hybrid (C1 rates [R-11, R-12] + last-season minutes + Marcel games [R-13]), added formally to the backtest with CIs, and gate on season-total value
  - B the same with Marcel rates
  - C ship B0 as the gate says
  - D build a minutes model first (1–2 days; empirical only, the RSCH-002 literature gap)

## G-25 · Users, profiles & settings (D-64)
**Status**: APPROVED (Q1 A Firestore + a BigQuery copy, Q2 A, Q3 A) — owner, 2026-10-02. See D-64.
- **Decided** (full menu with Learn/pros/cons/cost/CV in `architecture-decisions.md` D-64):
  - Q1 store: ★ A Firestore (free tier) · B JSON in the serve bucket · C Cloud SQL Postgres (~US$10/mo) · D BigQuery
  - Q2 access: ★ A invites + owner/member roles · B keep the env allowlist · C open sign-up
  - Q3 first slice: ★ A identity + profile + settings now, a second user's own league later · B everything at once · C owner-only settings
- **Answer**: `approve G-25 A,A,A` (or other letters).
- **Blocks**: APP-008, APP-009, WEB-014, WEB-015.

## G-26 · Missed games at replacement level (D-65)
**Status**: APPROVED (A, then B: "do both") — owner, 2026-10-02. Results: neither passed its pre-registered rule (DRAFT-011 −0.044, DRAFT-012 −0.102); values unchanged.
- Options: A replacement-filled missed games · B 3-season games/minutes smoothing · C both · D keep the model.
- Pre-registration and ship rules: DRAFT-011 (A), DRAFT-012 (B).
- **Blocks**: DRAFT-011, DRAFT-012 (both done).

## G-28 · Draft simulator (D-67)
**Status**: APPROVED (A, A, A) — owner, 2026-10-03: web page · calibrated styles · real timers + fast-forward
- **Options**: Q1 surface: A ★ web page · B practice mode in the HTML board. Q2 opponents: A ★ calibrated rule-based
  styles · B calibrated to Yahoo market prices (needs a login) · C learned tendencies (no data yet). Q3 pace: A ★ real
  timers + fast-forward · B untimed.
- **Blocks**: DRAFT-013, DRAFT-014, DRAFT-015.

## G-30 · Telegram linking and settings for the daily job (D-68)
**Status**: APPROVED (A, A) — owner, 2026-10-03: webhook with a secret header · a shared users package
- **Options**: Q1 transport: A ★ webhook with a secret header · B on-demand `getUpdates`. Q2 read path: A ★ move the
  users store into a shared package · B internal API route · C BigQuery mirror.
- **Blocks**: APP-009 AC3 (transport), APP-010.
## G-36 · Going public: personal data in git history, and the licence (SEC-001)
**Status**: APPROVED 2026-10-04 (owner: Q1 A fresh snapshot · Q2 A PolyForm Noncommercial 1.0.0 · Q3 publish). The audit found one real problem (below); everything else passed.
- **Why now**: GitHub Actions on the private repo fails on billing, so no PR can merge with green CI. A public repo gets
  Actions free (D-38 already plans this after SEC-001).
- **Found** (`SEC-001` Evidence): the full-history gitleaks scan is clean (484 commits) and the fixtures are synthetic. But
  the commit author on 402 of 543 commits is the owner's university student-ID email address, and the owner's
  personal email address is in 4 commits (a runbook, since replaced by a placeholder). Public means
  anyone can read and scrape both, permanently.
- **Learn**: a git commit stores its author email and every file version forever. Making a repo public publishes all of
  that. Rewriting history changes every commit ID, but GitHub also keeps hidden `refs/pull/*` copies of old commits for
  every PR, and only GitHub Support can purge those.
- **Q1 Options** (history):
  - **A ★ Fresh snapshot.** Rename the current repo to a private archive, then create a new public repo holding the
    current files as one commit authored by your GitHub noreply address. Pros: nothing old is published, no force-push,
    no Support ticket, free CI. Cons: the public repo has no commit history (the case study can still describe the
    process; the archive keeps it). Cost: US$0. Needs: re-pointing the Workload Identity condition if the repo name
    changes (Tier B, `terraform apply`), and the BRAND-002 rename can be done at the same time. **CV value**: a clean
    public repo with a README and case study reads better than a long history of task commits.
  - **B Rewrite history** with `git filter-repo` (map authors to noreply, replace the Gmail text), force-push, then go
    public. Pros: keeps all 543 commits. Cons: destructive and irreversible on `main`; every open PR and worktree must be
    redone; old commits stay reachable through hidden PR refs until GitHub Support purges them, so the email may stay
    exposed. Not recommended.
  - **C Accept the exposure** and publish as is. Cons: a permanent student-ID address and personal email in public
    metadata; spam and phishing risk. Not recommended.
- **Q2 Licence** (AC4): **A ★ PolyForm Noncommercial 1.0.0** (source-available: anyone can read and run it for
  non-commercial use; you keep the commercial rights, which matters for Courtside and the kanji project) · B MIT (maximum
  CV reach, but anyone may take and sell it) · C All rights reserved (no licence file; readable, not reusable).
- **Q3 Publish confirmation** (AC5): after Q1 and Q2 are done and `docs/` has been re-read by you, say "publish" and I
  set the new repo public and enable the `main` ruleset (required checks, no force-push).
- **Blocks**: SEC-001, free CI for every PR (#134, #135, #137 and later), SEC-002 follow-on.

## G-35 · Sign-in methods, user-data ruleset, spending and the rename (D-73, D-74)
**Status**: APPROVED 2026-10-04 (owner: "you have my approval for everything"): all ★ options, Q5 = 16+ (US and AU), D-75. Money items stay off: phone SMS off, no billing account yet, no Apple fee; the repo rename (BRAND-002) and the lawyer review stay owner actions.
- **Will ask**: Q1 methods (★ Google + email/password) · Q2 phone (★ built, off at launch) · Q3 Identity Platform upgrade
  (★ in dev when INFRA-009 starts) · Q4 browser token storage (★ SDK default + strict CSP + ADR) · Q5 minimum age (★ 16+
  with a checkbox; owner direction, D-75) · Q6 approve the standard (S-40) · Q7 dead-code and duplication tools (S-41). Also: approve a billing account and SMS
  spend if you choose phone; Apple developer fee if you choose Apple; the GitHub repository rename (BRAND-002).
- **Why it matters**: sign-up is the first place strangers can cost money (SMS) or harm users (takeover, data leaks). The
  owner dropped Yahoo (D-75, YAHOO-002) and does not want paid licences yet, so NBA data stays on the free sources while the
  app is personal (DATA-039); a commercial data licence is needed before ads or open sign-up. Legal items (Australian privacy and consumer law, the under-16 social media rules, fantasy-sports law,
  ads and player names, US breach law) need one lawyer review before open sign-up or ads; the research is not legal advice.
- **Blocks**: DATA-039 (no: may start now), YAHOO-002 (after the draft), INFRA-009, INFRA-010, APP-018..020, APP-024..027, WEB-036, WEB-037, SEC-002, SEC-003, HYG-002, BRAND-002.
  RSCH-010 is not gated but needs the owner's Google account for a throwaway Firebase project (review). The name
  Courtside is already approved (D-73): BRAND-001 and BRAND-003 are not gated.

## G-34 · Accounts and leagues (D-72)
**Status**: APPROVED 2026-10-04 (owner: "you have my approval for everything"): all ★ options.
- **Will ask**: Q1 who may register (★ open behind a flag, reviewed first) · Q2 sign-in methods (★ Google + email/password) ·
  Q3 pictures (★ uploads with server re-encode and report/hide) · Q4 league scope (★ shell; live draft and seasons later) ·
  Q5 phone navigation (★ no seventh tab). Plus the defaults listed at the end of D-72 (co-commissioner powers, default team name).
- **Why it matters**: Q1 reverses part of D-64 (invite-only). The live Yahoo data stays owner-only whichever you pick.
- **Blocks**: APP-012..017, APP-021..023, WEB-030..035, WEB-038. (Sign-in methods in Q2 are superseded by D-74 / G-35; SEC-002 is gated by G-35.)

## G-33 · League-specific valuation and scale targets (D-70, D-71)
**Status**: APPROVED (B; A, A, A) - owner, 2026-10-04: server on demand with cache · scale to zero · asyncio load script + Lighthouse CI · 25 concurrent users
- **Options**: D-70 (one question): A TS port · B ★ server on demand with cache · C precomputed presets. D-71: Q1 min
  instances · Q2 load and web-perf tooling (and its CI job) · Q3 SLO targets.
- **Blocks**: DRAFT-018, PERF-001, PERF-002 (and so DRAFT-019 for non-default leagues).

## G-32 · ML plan amendment: returners after a lost season (DRAFT-022)
**Status**: APPROVED - owner, 2026-10-04 (the evaluation must finish by Thu 15 Oct to affect the 18 Oct draft)
- **Will ask**: approve the pre-registration in `DRAFT-022-return-from-lost-season-games.md` (cohort definition, variant R,
  three-part ship rule) as an amendment to the ML plan. You approve the test, not the outcome. Prompted by the Damian Lillard
  case ($1, projected 26 of 82 games after a lost season). Fallback if declined or it fails: cited override rows (DATA-036).
- **Blocks**: DRAFT-022.

## G-31 · Season replay (D-69)
**Status**: APPROVED (all A) — owner, 2026-10-04: published files + browser simulation · daily lineups (auto default) · rivals auto-start, no pickups · next-day pickups · last three seasons
- **Options**: Q1 data: A ★ published files, browser simulates · B server simulates. Q2 lineups: A ★ daily · B weekly.
  Q3 rivals: A ★ auto lineups, no pickups · B greedy streaming. Q4 waivers: A ★ next day · B 2-day period.
  Q5 seasons: A ★ last three · B all since 2016-17.
- **Blocks**: SIM-001…SIM-004.

## G-29 · ML plan amendment: team/coach context (EXP-004)
**Status**: NOT NEEDED (ANL-010 NO-GO, 2026-10-03) — opened only if ANL-010's pre-registered go/no-go says "go"
- **Will ask**: approve EXP-004's completed pre-registration (variant, ship rule) as an amendment to the ML plan.
- **Blocks**: EXP-004.

## G-27 · Monitoring and alerts (D-66)
**Status**: APPROVED (A) — owner, 2026-10-03
- **Decided**: A ★ watchdog job · B Cloud Monitoring + Telegram webhook · C both (watchdog + uptime checks to email).
- **Also needed from you**: the billing account for a budget alert (50/90/100 % of US$10/month), and `terraform apply`.
- **Blocks**: INFRA-005.

## G-23 · ML plan amendment: minutes model + breakout probability
**Status**: APPROVED — 2026-09-26 (panels: both minutes models with dev/holdout selection; breakout = +50 ranks into the top 150; logistic regression; flags only if proven; D-54)
- Owner decision D-53 (2026-09-25). The amendment to docs/architecture/ml-methodology-plan.md (a component card for each model, features, validation, metrics, pre-registered ship rules) is presented as panels with verified [R-xx] from RSCH-006.
- **Blocks**: DRAFT-007.

## G-24 · ML plan amendment: pre-season and news breakout signals
**Status**: APPROVED — 2026-09-26 (panels: minutes + starts; cutoff 2 days pre-opener; same ship rules as D-54/D-55; news spike capped at US$5; D-57)
- Owner decision D-56 (2026-09-26). Covers: the pre-season signal (features, pre-draft cutoff equivalence, ship rule), then the LLM news reader (sources, extraction schema, historical validation). Presented as panels with verified [R-xx] from RSCH-007.
- **Blocks**: DATA-030 (ingest waits for research, per the owner), DRAFT-008, DISC-012.

## G-22 · Data design, draft slice
**Status**: APPROVED — 2026-09-25 (after a walk-through; Q1 both, Q2 overrides file, Q3 apply after plan review)
- Covers: stats.nba.com history (3 seasons) + the CDN schedule + the imported league settings → a raw → staging → player-pool → projection-input flow, with lineage and checks.
- **Blocks**: DRAFT-001.

## G-20 · Data pipeline design approval
**Status**: PENDING
- **Owner requirement (2026-09-25)**: once all raw data sources are confirmed, present the proposed data pipeline architecture and layers, and how they feed the models, for approval before building.
- **Decision**: approve `docs/architecture/data-pipeline-design.md` (DATA-000): the source inventory, the layer-by-layer table catalogue (grain, keys, as-of columns, freshness, DQ tests), lineage diagrams, and the mapping from marts/features to each model and decision component.
- **Sequencing**:
  - The sources are confirmed after the NBA spikes (DISC-003/004/005 ✅), the Yahoo spikes (DISC-001/002: needs the owner's one-time consent), and ID matching (DISC-006).
  - **Raw capture (DATA-001…DATA-011) is not blocked**, because the design is already approved (immutable raw snapshots, ADR-0005/0020) and M1 is time-critical.
  - **Everything that shapes data beyond raw is blocked** (dbt staging/intermediate/marts, feature views).
- **Blocks**: DATA-012…DATA-023, ANL-001…ANL-004, ANL-008, ML-001, DRAFT-001 (the draft's pool shaping).

## G-19 · ML methodology plan approval
**Status**: APPROVED (all ★ in §24: distributions + simulation first; holdout = 2025-26 second half; add/drop = this week + discounted next week; statistical models only this season) — 2026-09-28
- **Owner mandate (2026-09-25)**: the ML design must be explicitly grounded in **verified** academic literature, with a fully fleshed-out plan approved before implementation.
- **Decision**: approve `docs/architecture/ml-methodology-plan.md` (RSCH-004), built only on references verified in RSCH-001. Review happens via panels: one per component group, with citations.
- **Ready for review (2026-09-28)**: the draft components were approved separately (G-21, G-23, G-24). The in-season plan is Part 2 of `ml-methodology-plan.md` (§14-24). Answer the 4 questions in §24 to approve.
- **Blocks**: all ML-*, DEC-002…DEC-008, ANL-005, ANL-006, EVAL-003/004, DRAFT-002, DRAFT-003, DRAFT-005.

## G-18 · iOS app phase (future)
**Status**: PENDING
- **Decision** (only when the iOS phase starts): the macOS build route (GitHub Actions macOS runners / Xcode Cloud / a Mac) and the Apple Developer Program fee (US$99/yr, above the G-08 monthly ceiling if you include it).
- **Blocks**: future iOS tasks (not yet in the backlog).

## G-16 · Dashboard access / security model
**Status**: APPROVED (app-level login; see D-27) — 2026-09-24
- **Options**:
  - A. Reachable only on your Tailscale network, with no app login (free)
  - B. A public URL behind Cloudflare Access (free; email login)
  - C. A public URL with app-level auth
- **Recommendation**: A.
- **Blocks**: PROD-007.
