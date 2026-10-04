---
name: status
description: Report project status, or why a specific task is blocked. Use when the owner asks "what's the status", "where are we", "why is <ID> blocked", or at the start of a session.
arguments: [task_id]
metadata:
  version: 0.1.0
  inputs: "optional task ID"
  outputs: "phone-length status report"
---

## Current state (injected)
!`python tools/tasks.py status`

## Procedure
1. If a task ID was given (`$task_id`), run `python tools/tasks.py why $task_id`. Explain each blocker in plain language, and say what would unblock it (which task, or which gate the owner must answer).
2. Otherwise, read `docs/project/STATUS.md` and combine it with the injected output above.

## Output (≤ 12 lines, conclusion first)
- Phase and the latest milestone
- What's in progress
- The top 3 next eligible tasks
- Pending gates, with ⏰ time-critical ones first
- Risks, if any changed

## Must not
- Modify any files.
- Read architecture or standards docs (not needed for status).
