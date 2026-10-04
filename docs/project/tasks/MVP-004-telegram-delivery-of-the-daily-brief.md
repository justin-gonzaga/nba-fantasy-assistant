---
id: MVP-004
title: "Telegram delivery of the daily brief"
epic: EP-12 In-season MVP
phase: 5
component: mvp
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [MVP-003]
areas: [apps/pipeline/**, packages/core/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# MVP-004 — Telegram delivery of the daily brief

## Objective
Send the brief to the owner's Telegram chat through the bot token in .env (never printed or logged).

## Context to read (only these)
- docs/project/STATUS.md (MVP plan)

## Acceptance criteria
- [x] AC1: A sender with a fake transport under test; the token is read from settings, never logged
      Verify: tests
- [x] AC2: A live test message reaches the owner
      Verify: the owner confirms

## Test requirements
TDD; offline tests with fixtures.

## Evaluation requirements
Baselines only (no new ML); anything measured is reported with CIs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | apps/pipeline/tests/test_telegram.py (5): Markdown send, plain-text fallback on 400, errors never contain the token, chat-id discovery, splitting long messages | ✅ |
| AC2 | live | 2026-09-28: the owner messaged the bot; `telegram-setup` saved the chat; `send-brief` delivered a sample brief (1,133 characters). The first test used a stale week table: fixed by the as_of_day guard (a brief refuses a week table from another day) | ✅ |

## Implementation history
- 2026-09-28: `fantasy_pipeline.telegram` + CLI `telegram-setup`, `send-brief`. Live check: the token works; waiting for the owner's first message to the bot.

## Decisions
- MVP plan (owner, 2026-09-27): a daily Telegram brief from tip-off (20 Oct), baselines only.

## Known issues
_None._

## Follow-ups
_None._
