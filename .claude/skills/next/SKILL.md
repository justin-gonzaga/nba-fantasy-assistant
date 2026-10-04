---
name: next
description: Recommend what to work on next. Use when the owner asks "what should I/we work on next" or "what's unblocked".
metadata:
  version: 0.1.0
  outputs: "top eligible tasks with one-line reasons"
---

## Eligible tasks (computed by script)
!`python tools/tasks.py next -n 5`

## Pending gates
!`python tools/tasks.py gates`

## Procedure
1. Present the top 3 eligible tasks, each with a one-line "why now" (critical path to a milestone, how much it unblocks, and its size).
2. If a pending gate blocks more valuable work than any eligible task, say so and name the gate. The owner answering it may be the best "next task".
3. Offer: "Say `/work-task <ID>` to start."

## Must not
- Pick tasks by your own reasoning over the files. The script's order is authoritative, and you may only add context.
