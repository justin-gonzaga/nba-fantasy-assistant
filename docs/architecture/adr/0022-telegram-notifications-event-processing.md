# ADR-0022: Telegram bot as the primary interface; poll-and-react event processing; awake window

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: D-33 A, D-34 B, D-35 A, U1, U6, S-28 D, NFR10
- **Related**: system-architecture §4.4, §6

## Context
No source pushes events. The owner decides only while awake and wants phone notifications, and later a native app.

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
- Pollers run on a schedule. Content-hash change detection feeds an in-process event queue, which triggers a targeted recompute. A notification is sent only when a recommendation materially changes.
- **Telegram bot** (two-way) delivers alerts, digests and answers to questions, with compact messages and buttons. System alerts go to the same bot.
- Advise-only (no automatic Yahoo moves).
- User-facing work runs only inside each user's awake window.

## Consequences
- Cheap and responsive during decision hours.
- The Telegram bot needs a webhook endpoint on the API service.

## Revisit triggers
Missed actionable news during the awake window, or the move to the iOS app (APNs).
