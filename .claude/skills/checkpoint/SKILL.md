---
name: checkpoint
description: Write a resumable handoff into the current task file before stopping mid-task (context getting long, session ending, blocked). Use when stopping work that isn't finished.
metadata:
  version: 0.1.0
  outputs: "Implementation-history checkpoint entry; WIP commit"
---

## Procedure
1. Identify the in-progress task (`python tools/tasks.py status`).
2. Commit the work in progress on the task branch (`chore: WIP checkpoint`, `Task: <ID>`), even if tests fail. Never commit to main.
3. Append to the task file's *Implementation history*:
   ```
   ### <date> checkpoint
   - Branch: task/<ID>-...  (last commit <sha>)
   - Done: <ACs done, with evidence>
   - Next step: <the exact next action>
   - Open questions / blockers: <…>
   - Attempts so far: <n>
   ```
4. If blocked on the owner, set `status: blocked` and add or refer to a gate entry.
5. Tell the owner, in one line, how to resume: `/work-task <ID>`.
