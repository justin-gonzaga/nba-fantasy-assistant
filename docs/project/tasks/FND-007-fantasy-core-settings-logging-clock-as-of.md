---
id: FND-007
title: "fantasy_core: settings, logging, clock/as-of, errors"
epic: EP-10 Foundation
phase: 1
component: core
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [FND-002]
areas: [packages/core/**]
standards: [python, software-engineering, testing]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# FND-007 — fantasy_core: settings, logging, clock/as-of, errors

## Objective
Shared foundations every package uses.

## Context to read (only these)
- `docs/standards/software-engineering.md`
- `docs/standards/python.md`

## Acceptance criteria
- [x] AC1: `Settings` (pydantic-settings) loads APP_ENV, DATA_ROOT, GCP_PROJECT, YAHOO_LEAGUE_KEY, USER_TZ and the awake window, with validation. Secrets are `SecretStr` and never appear in repr/logs. Non-secret keys are documented in `env.example`.
      Verify: packages/core/tests/test_settings.py (defaults, env override, invalid tz → ConfigError, secret masked in repr)
- [x] AC2: structlog logging renders JSON outside local and pretty console locally. `bind_context(run_id, task, job)` context appears on every event. Keys that look like secrets are redacted.
      Verify: packages/core/tests/test_logging.py (JSON fields present, context bound, redaction)
- [x] AC3: The `Clock` protocol has `SystemClock` + `FrozenClock` (advance). `AsOf` rejects naive datetimes and normalises to UTC.
      Verify: packages/core/tests/test_clock.py (+ hypothesis: any aware datetime → AsOf in UTC with the same instant)
- [x] AC4: NBA game-date helpers: `game_date(ts)` (US/Eastern calendar date) and `et_day_bounds_utc(d)`. They are correct across DST (23/24/25-hour days).
      Verify: packages/core/tests/test_gamedate.py (hypothesis: bounds contain ts; day length ∈ {23,24,25} h; known DST dates)
- [x] AC5: The error hierarchy (`FantasyError` → ConfigError, SourceUnavailable, ContractViolation, LeakageError) matches the software-engineering standard.
      Verify: packages/core/tests/test_errors.py
- [x] AC6: fantasy_core coverage is ≥ 90 %, and ruff + mypy --strict are clean.
      Verify: `just ci-local` → coverage report for packages/core ≥ 90 %

## Test requirements
Unit + hypothesis (timezone/DST).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | packages/core/tests/test_settings.py (6 tests: defaults, env override, invalid tz, invalid env, secret masking, cached get_settings) | pass; `env.example` documents the non-secret keys |
| AC2 | test | packages/core/tests/test_logging.py (JSON + context, top-level and nested redaction, console locally) | 4 pass |
| AC3 | test | packages/core/tests/test_clock.py (incl. hypothesis same-instant UTC normalisation; naive → NaiveDatetimeError) | pass |
| AC4 | test | packages/core/tests/test_gamedate.py (2026-03-08 = 23 h, 2026-11-01 = 25 h, 2026-11-02 = 24 h; hypothesis 2015–2040 bounds contain the instant) | pass (DST dates independently confirmed by the reviewer) |
| AC5 | test | packages/core/tests/test_errors.py | pass: FantasyError → ConfigError, SourceUnavailable, ContractViolation, NaiveDatetimeError, LeakageError |
| AC6 | command | `just ci-local` | ruff/format/mypy strict clean; 35 passed; coverage 100 % (≥ 90) |

## Implementation history
### 2026-09-25 — overnight session (loop)
- TDD: wrote 5 test modules first (red: import errors), then implemented settings, logging, clock, gamedate and errors. Added deps: pydantic-settings, structlog, tzdata (Windows needs tzdata for zoneinfo).
- **Outside `areas:` (DoD §1)**: `env.example` (documents the non-secret Settings keys); root `pyproject.toml` (ruff `src` globs so first-party imports sort correctly; test-only ignores S105/S106 for fake secrets; N818 exemption for the standard's own error names).
- Review round 1: FAIL on process only (the Evidence/history weren't filled before review; the code was verified correct). Fixed, plus the reviewer's suggestions: **nested secret redaction** in logs, and a specific `NaiveDatetimeError` instead of the base error.
- Process lesson → the work-task skill now fills Evidence *before* the review step.
- Attempts: 2 review rounds. Interventions: none.

## Decisions
- `load_settings(env_file=None)` is the test entry point (avoids the pydantic-settings `_env_file` kwarg typing issue).
- Naive datetimes raise `NaiveDatetimeError` (added to the error hierarchy).

## Known issues
_None._

## Follow-ups
_None._
