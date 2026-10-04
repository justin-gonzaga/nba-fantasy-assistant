#!/usr/bin/env python3
"""Task CLI for the in-repo markdown task system (ADR-0015).

Stdlib only, so it runs before the uv workspace exists.
Usage: python tools/tasks.py {validate|next|show|why|board|status|gates|claim|done} [...]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_DIR = ROOT / "docs" / "project" / "tasks"
GATES_FILE = ROOT / "docs" / "project" / "human-approval-gates.md"
BOARD_FILE = TASK_DIR / "BOARD.md"

STATUSES = {"todo", "in_progress", "blocked", "review", "done", "cancelled"}
AUTONOMY = {"auto", "review", "gated"}
SIZES = {"S", "M"}
REQUIRED = ["id", "title", "epic", "phase", "status", "ready", "size", "autonomy", "depends_on"]
ID_RE = re.compile(r"^[A-Z]{2,5}-\d{3}$")


@dataclass
class Task:
    path: Path
    meta: dict[str, object]
    body: str
    dependents: set[str] = field(default_factory=set)

    @property
    def id(self) -> str:
        return str(self.meta["id"])

    @property
    def status(self) -> str:
        return str(self.meta["status"])

    @property
    def deps(self) -> list[str]:
        raw = self.meta.get("depends_on")
        return [str(x) for x in raw] if isinstance(raw, list) else []

    @property
    def gate(self) -> str | None:
        g = self.meta.get("gate")
        return None if g in (None, "", "none") else str(g)

    @property
    def phase(self) -> int:
        return int(str(self.meta["phase"]))


def _parse_value(raw: str) -> object:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [s.strip().strip("'\"") for s in inner.split(",") if s.strip()] if inner else []
    if raw in ("true", "false"):
        return raw == "true"
    return raw.strip("'\"")


def parse_task(path: Path) -> Task:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: missing front matter")
    meta: dict[str, object] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_value(value)
    return Task(path, meta, m.group(2))


def load_tasks() -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for p in sorted(TASK_DIR.glob("*.md")):
        if p.name in {"README.md", "BOARD.md", "_template.md"}:
            continue
        t = parse_task(p)
        tasks[t.id] = t
    for t in tasks.values():
        for d in t.deps:
            if d in tasks:
                tasks[d].dependents.add(t.id)
    return tasks


def load_gates() -> dict[str, str]:
    gates: dict[str, str] = {}
    if not GATES_FILE.exists():
        return gates
    current = None
    for line in GATES_FILE.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^## (G-\d{2})\b", line)
        if h:
            current = h.group(1)
            continue
        s = re.match(r"^\*\*Status\*\*:\s*(.+)$", line)
        if s and current:
            gates[current] = s.group(1).strip()
            current = None
    return gates


def gate_ok(gate: str | None, gates: dict[str, str]) -> bool:
    return gate is None or gates.get(gate, "").upper().startswith("APPROVED")


def blockers(t: Task, tasks: dict[str, Task], gates: dict[str, str]) -> list[str]:
    reasons = []
    if t.meta.get("ready") is not True:
        reasons.append("not refined yet (ready: false) - run /new-task refine")
    for d in t.deps:
        if d not in tasks:
            reasons.append(f"unknown dependency {d}")
        elif tasks[d].status != "done":
            reasons.append(f"waits on {d} ({tasks[d].status})")
    if not gate_ok(t.gate, gates):
        reasons.append(f"gate {t.gate} is {gates.get(t.gate or '', 'missing')}")
    if t.status == "blocked":
        reasons.append("explicitly blocked - see task file")
    return reasons


def transitive_dependents(tid: str, tasks: dict[str, Task]) -> int:
    seen: set[str] = set()
    stack = [tid]
    while stack:
        for d in tasks[stack.pop()].dependents:
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return len(seen)


def eligible(tasks: dict[str, Task], gates: dict[str, str]) -> list[Task]:
    out = [t for t in tasks.values() if t.status == "todo" and not blockers(t, tasks, gates)]
    # Earliest phase first, then tasks that unblock the most work (critical path), then ID.
    return sorted(out, key=lambda t: (t.phase, -transitive_dependents(t.id, tasks), t.id))


AC_RE = re.compile(r"^- \[[ xX]\] (AC\d+):", re.M)
REQUIRED_SECTIONS = [
    "## Objective",
    "## Acceptance criteria",
    "## Test requirements",
    "## Evidence",
]


# Tasks a person uses (pages, endpoints) spell out who uses them and what can go wrong (IMP-006).
USER_FACING = {"web", "api"}
STORIES = "## User stories and edge cases"


def _section(body: str, heading: str) -> str:
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def spec_issues(t: Task) -> tuple[list[str], list[str]]:
    """Task specification standard (T1-T3): returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    if t.status == "cancelled" or t.meta.get("ready") is not True:
        return errors, warnings
    strict = t.status in {"review", "done"}
    for sec in REQUIRED_SECTIONS:
        if sec not in t.body:
            (errors if strict else warnings).append(f"{t.id}: missing section '{sec}'")
    if t.meta.get("component") in USER_FACING and t.status != "done" and STORIES not in t.body:
        msg = f"{t.id}: user-facing task has no '{STORIES}'"
        (errors if strict else warnings).append(msg)
    acs = _section(t.body, "## Acceptance criteria")
    ids = AC_RE.findall(acs)
    if not ids:
        errors.append(f"{t.id}: ready task has no '- [ ] ACn:' criteria")
    chunks = AC_RE.split(acs)[1:]  # [id, text, id, text, ...]
    for ac_id, text in zip(chunks[0::2], chunks[1::2], strict=False):
        if "Verify:" not in text:
            (errors if strict else warnings).append(f"{t.id}: {ac_id} has no 'Verify:' line")
    if t.status == "done":
        ev = _section(t.body, "## Evidence")
        for ac_id in ids:
            if not re.search(rf"^\|\s*{ac_id}\s*\|", ev, re.M):
                errors.append(f"{t.id}: done but no Evidence row for {ac_id}")
    return errors, warnings


def cmd_validate(
    tasks: dict[str, Task], gates: dict[str, str], verbose_warnings: bool = False
) -> int:
    errors = []
    warnings: list[str] = []
    for t in tasks.values():
        e, w = spec_issues(t)
        errors += e
        warnings += w
        for k in REQUIRED:
            if k not in t.meta:
                errors.append(f"{t.id}: missing '{k}'")
        if not ID_RE.match(t.id):
            errors.append(f"{t.id}: bad id format")
        if not t.path.name.startswith(t.id):
            errors.append(f"{t.id}: filename must start with the id")
        if t.status not in STATUSES:
            errors.append(f"{t.id}: bad status {t.status}")
        if t.meta.get("autonomy") not in AUTONOMY:
            errors.append(f"{t.id}: bad autonomy")
        if t.meta.get("size") not in SIZES:
            errors.append(f"{t.id}: size must be S or M (split L tasks)")
        if t.gate and t.gate not in gates:
            errors.append(f"{t.id}: unknown gate {t.gate}")
        errors += [f"{t.id}: unknown dependency {d}" for d in t.deps if d not in tasks]
        if t.meta.get("ready") is True and "## Acceptance criteria" not in t.body:
            errors.append(f"{t.id}: ready task needs '## Acceptance criteria'")
    # cycle detection
    state: dict[str, int] = {}

    def visit(n: str, trail: list[str]) -> None:
        if state.get(n) == 1:
            errors.append("cycle: " + " -> ".join([*trail, n]))
            return
        if state.get(n) == 2 or n not in tasks:
            return
        state[n] = 1
        for d in tasks[n].deps:
            visit(d, [*trail, n])
        state[n] = 2

    for n in tasks:
        visit(n, [])
    for err in errors:
        print("ERROR", err)
    if verbose_warnings:
        for warn in warnings:
            print("WARN ", warn)
    print(f"{len(tasks)} tasks, {len(errors)} errors, {len(warnings)} warnings (-w to list)")
    return 1 if errors else 0


def cmd_next(tasks: dict[str, Task], gates: dict[str, str], n: int) -> int:
    el = eligible(tasks, gates)
    if not el:
        print("No eligible tasks. Pending gates / blocked work:")
        cmd_gates(gates)
        return 0
    for t in el[:n]:
        print(
            f"{t.id}  [P{t.phase} {t.meta['size']} {t.meta['autonomy']}]  {t.meta['title']}"
            f"  (unblocks {transitive_dependents(t.id, tasks)})"
        )
    return 0


def cmd_show(tasks: dict[str, Task], gates: dict[str, str], tid: str) -> int:
    t = tasks.get(tid)
    if not t:
        print(f"unknown task {tid}")
        return 1
    print(t.path.relative_to(ROOT))
    for k, v in t.meta.items():
        print(f"  {k}: {v}")
    b = blockers(t, tasks, gates)
    print("  blockers:", "; ".join(b) if b else "none")
    print("  dependents:", ", ".join(sorted(t.dependents)) or "none")
    return 0


def cmd_gates(gates: dict[str, str]) -> int:
    for g, s in gates.items():
        if not s.upper().startswith("APPROVED"):
            print(f"{g}: {s}")
    return 0


def cmd_status(tasks: dict[str, Task], gates: dict[str, str]) -> int:
    counts: dict[str, int] = {}
    for t in tasks.values():
        counts[t.status] = counts.get(t.status, 0) + 1
    print("Tasks:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    wip = [t for t in tasks.values() if t.status == "in_progress"]
    for t in wip:
        print(f"IN PROGRESS {t.id} ({t.meta.get('assignee', '?')}): {t.meta['title']}")
    pending = [g for g, s in gates.items() if not s.upper().startswith("APPROVED")]
    print(f"Pending gates ({len(pending)}): {', '.join(pending) or 'none'}")
    print("Next eligible:")
    cmd_next(tasks, gates, 3)
    return 0


def cmd_board(tasks: dict[str, Task], gates: dict[str, str]) -> int:
    lines = [
        "# Task Board",
        "",
        "_Generated by `python tools/tasks.py board`. Do not edit by hand._",
        "",
    ]
    for phase in sorted({t.phase for t in tasks.values()}):
        lines += [
            f"## Phase {phase}",
            "",
            "| ID | Title | Status | Size | Tier | Gate | Depends on | Blockers |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for t in sorted((t for t in tasks.values() if t.phase == phase), key=lambda t: t.id):
            b = "" if t.status == "done" else "; ".join(blockers(t, tasks, gates))
            lines.append(
                f"| [{t.id}]({t.path.name}) | {t.meta['title']} | {t.status} | {t.meta['size']}"
                f" | {t.meta['autonomy']} | {t.gate or ''} | {', '.join(t.deps)} | {b} |"
            )
        lines.append("")
    BOARD_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {BOARD_FILE.relative_to(ROOT)}")
    return 0


def _set_fields(t: Task, **fields: str) -> None:
    text = t.path.read_text(encoding="utf-8")
    head, _, rest = text[4:].partition("\n---\n")
    for k, v in fields.items():
        if re.search(rf"^{k}:", head, re.M):
            head = re.sub(rf"^{k}:.*$", f"{k}: {v}", head, flags=re.M)
        else:
            head += f"\n{k}: {v}"
    t.path.write_text(f"---\n{head}\n---\n{rest}", encoding="utf-8")


def cmd_claim(tasks: dict[str, Task], gates: dict[str, str], tid: str, by: str) -> int:
    t = tasks[tid]
    if t.status == "in_progress" and t.meta.get("assignee") not in (None, "", by):
        print(f"{tid} already claimed by {t.meta.get('assignee')}")
        return 1
    b = blockers(t, tasks, gates)
    if b and t.status != "in_progress":
        print("cannot claim:", "; ".join(b))
        return 1
    _set_fields(t, status="in_progress", assignee=by)
    print(f"claimed {tid}")
    return 0


def cmd_done(tasks: dict[str, Task], gates: dict[str, str], tid: str) -> int:
    t = tasks[tid]
    # Snapshot eligibility before the in-memory status flip, or dependents look already unblocked.
    before = {x.id for x in eligible(tasks, gates)}
    t.meta["status"] = "done"  # check the evidence as if done, before writing
    errs, _ = spec_issues(t)
    if errs:
        print("cannot mark done (task spec standard):")
        for e in errs:
            print("  -", e)
        return 1
    _set_fields(t, status="done", completed=dt.datetime.now(dt.UTC).date().isoformat())
    tasks = load_tasks()
    newly = [x.id for x in eligible(tasks, gates) if x.id not in before]
    print(f"{tid} done. Newly unblocked: {', '.join(newly) or 'none'}")
    return cmd_board(tasks, gates)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate").add_argument("-w", action="store_true", help="list warnings")
    p = sub.add_parser("next")
    p.add_argument("-n", type=int, default=3)
    for name in ("show", "why", "done"):
        sub.add_parser(name).add_argument("id")
    p = sub.add_parser("claim")
    p.add_argument("id")
    p.add_argument("--by", default="claude")
    sub.add_parser("board")
    sub.add_parser("status")
    sub.add_parser("gates")
    a = ap.parse_args()
    tasks, gates = load_tasks(), load_gates()
    match a.cmd:
        case "validate":
            return cmd_validate(tasks, gates, a.w)
        case "next":
            return cmd_next(tasks, gates, a.n)
        case "show" | "why":
            return cmd_show(tasks, gates, a.id)
        case "board":
            return cmd_board(tasks, gates)
        case "status":
            return cmd_status(tasks, gates)
        case "gates":
            return cmd_gates(gates)
        case "claim":
            return cmd_claim(tasks, gates, a.id, a.by)
        case "done":
            return cmd_done(tasks, gates, a.id)
    return 2


if __name__ == "__main__":
    sys.exit(main())
