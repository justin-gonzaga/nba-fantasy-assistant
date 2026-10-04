---
name: gate
description: List pending human-approval gates, or record the owner's decision on a gate ("approve G-05 A", "reject G-09", "discuss G-04", "accept all recommended"). Use whenever the owner answers or asks about decisions needing their input.
arguments: [action, gate, option]
metadata:
  version: 0.1.0
  inputs: "list | approve G-xx <option> | reject G-xx | defer G-xx | discuss G-xx"
  outputs: "updated gates file, ADR statuses, unblocked tasks"
---

Gates file: `docs/project/human-approval-gates.md`.
Decision menus:
- `docs/project/architecture-decisions.md` (D-xx, gate G-17)
- `docs/project/standards-decisions.md` (S-xx, gate G-10)

The owner may answer menu items directly ("D-12 A", "S-07 B", "explain D-19", "compare D-16 A vs C"):
- **Selections**: record each choice under the item as `**Selected**: <option> — <date>`. When every item in a menu is chosen, mark its gate APPROVED.
- **explain / compare**: a teaching answer of ≤ 25 lines covering the concept, a concrete fantasy example, the trade-offs, and the `[R-xx]` references for ML items. No file changes.

## Procedure
**list**
1. Run `python tools/tasks.py gates`.
2. Show the pending gates as a compact list with the ⏰ items first: one line each (decision + recommendation). Read only the summary table of the gates file.

**discuss G-xx**
1. Read only that gate's section.
2. Explain the options, the trade-offs, and the recommendation in ≤ 15 lines. For ML gates, include the `[R-xx]` references with a one-line justification each.

**approve / reject / defer G-xx [option]**
1. Only act on an explicit owner instruction in this conversation. Never infer approval.
2. Edit the gate's `**Status**:` line to `APPROVED (<option>) — <date>`, `REJECTED — <date>`, or `DEFERRED — <date>`. Update the summary-table row to match.
3. If a linked ADR exists, set its status (Accepted/Rejected), and update the ADR index.
4. If the chosen option differs from the recommendation, list the docs and tasks that must change. Then create a task (`/new-task`, or add a follow-up) to propagate the change. Do not rewrite the architecture inline.
5. For G-10, record each S-xx choice in `standards-decisions.md`. STD-001 then applies them.
6. Run `python tools/tasks.py board`, then `python tools/tasks.py next`, and report what became unblocked.
7. Commit with the message `docs(project): record owner decision on G-xx`. This is a Tier B change, but the owner's instruction is the approval.

## Must not
- Approve anything on the owner's behalf, or treat "sounds good" about a *different* gate as approval.
- Change the gate options themselves while recording a decision.
