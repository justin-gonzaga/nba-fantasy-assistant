"""Tests for the markdown task CLI (tools/tasks.py, FND-004).

Every test runs against a temporary task directory: the module-level paths are monkeypatched.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from tools import tasks

GOOD_BODY = """# {id}

## Objective
Do the thing.

## Acceptance criteria
- [ ] AC1: the thing is done
      Verify: `echo ok` -> ok

## Test requirements
pytest.

## Evidence
{evidence}

## Implementation history
_None yet._
"""

GATES = """# Gates

## G-01 Approved thing
**Status**: APPROVED (A)

## G-02 Pending thing
**Status**: PENDING
"""

WriteTask = Callable[..., Path]


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    task_dir = tmp_path / "docs" / "project" / "tasks"
    task_dir.mkdir(parents=True)
    gates = tmp_path / "docs" / "project" / "human-approval-gates.md"
    gates.write_text(GATES, encoding="utf-8")
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    monkeypatch.setattr(tasks, "TASK_DIR", task_dir)
    monkeypatch.setattr(tasks, "GATES_FILE", gates)
    monkeypatch.setattr(tasks, "BOARD_FILE", task_dir / "BOARD.md")
    return task_dir


def _task_text(tid: str, body: str | None = None, evidence: str = "", **meta: str | None) -> str:
    fields: dict[str, str | None] = {
        "id": tid,
        "title": f'"Title {tid}"',
        "epic": "EP-10 Foundation",
        "phase": "1",
        "status": "todo",
        "ready": "true",
        "size": "S",
        "autonomy": "auto",
        "gate": "none",
        "depends_on": "[]",
        "assignee": "",
    }
    fields.update(meta)
    head = "\n".join(f"{k}: {v}" for k, v in fields.items() if v is not None)
    text = body if body is not None else GOOD_BODY.format(id=tid, evidence=evidence)
    return f"---\n{head}\n---\n{text}"


@pytest.fixture
def write_task(repo: Path) -> WriteTask:
    def _write(tid: str, body: str | None = None, evidence: str = "", **meta: str | None) -> Path:
        path = repo / f"{tid}-slug.md"
        path.write_text(_task_text(tid, body, evidence, **meta), encoding="utf-8")
        return path

    return _write


def _load() -> tuple[dict[str, tasks.Task], dict[str, str]]:
    return tasks.load_tasks(), tasks.load_gates()


# ------------------------------------------------------------------ parsing


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("[A-001, 'B-002', \"C-003\"]", ["A-001", "B-002", "C-003"]),
        ("[]", []),
        ("[ ]", []),
        ("true", True),
        ("false", False),
        (' "Quoted title" ', "Quoted title"),
        ("", ""),
    ],
)
def test_parse_value(raw: str, expected: object) -> None:
    assert tasks._parse_value(raw) == expected


def test_parse_task_front_matter(repo: Path) -> None:
    path = repo / "FND-100-x.md"
    path.write_text(
        '---\nid: FND-100\n# a comment\n\ntitle: "A: colon title"\nready: true\n'
        "depends_on: [FND-001, FND-002]\ngate: G-01\nphase: 2\n---\nbody text\n",
        encoding="utf-8",
    )
    t = tasks.parse_task(path)
    assert t.id == "FND-100"
    assert t.meta["title"] == "A: colon title"
    assert t.meta["ready"] is True
    assert t.deps == ["FND-001", "FND-002"]
    assert t.gate == "G-01"
    assert t.phase == 2
    assert t.body == "body text\n"


def test_parse_task_without_front_matter_raises(repo: Path) -> None:
    path = repo / "FND-101-x.md"
    path.write_text("# no front matter\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing front matter"):
        tasks.parse_task(path)


def test_task_defaults_for_missing_deps_and_gate(repo: Path) -> None:
    t = tasks.Task(repo / "X.md", {"id": "X-001", "gate": "none"}, "")
    assert t.deps == []
    assert t.gate is None


def test_load_tasks_skips_special_files_and_links_dependents(write_task: WriteTask) -> None:
    write_task("FND-001")
    write_task("FND-002", depends_on="[FND-001]")
    for name in ("README.md", "BOARD.md", "_template.md"):
        (tasks.TASK_DIR / name).write_text("not a task\n", encoding="utf-8")
    loaded = tasks.load_tasks()
    assert sorted(loaded) == ["FND-001", "FND-002"]
    assert loaded["FND-001"].dependents == {"FND-002"}


def test_load_gates(repo: Path) -> None:
    assert tasks.load_gates() == {"G-01": "APPROVED (A)", "G-02": "PENDING"}


def test_load_gates_missing_file(repo: Path) -> None:
    tasks.GATES_FILE.unlink()
    assert tasks.load_gates() == {}


# ------------------------------------------------------------------ blockers / eligibility


def test_unblocked_task_has_no_blockers(write_task: WriteTask) -> None:
    write_task("FND-001", status="done")
    write_task("FND-002", depends_on="[FND-001]", gate="G-01")
    t, g = _load()
    assert tasks.blockers(t["FND-002"], t, g) == []


def test_blockers_report_every_reason(write_task: WriteTask) -> None:
    write_task("FND-001", status="in_progress")
    write_task("FND-002", depends_on="[FND-001, FND-999]", gate="G-02", ready="false")
    write_task("FND-003", gate="G-09", status="blocked")
    t, g = _load()
    assert tasks.blockers(t["FND-002"], t, g) == [
        "not refined yet (ready: false) - run /new-task refine",
        "waits on FND-001 (in_progress)",
        "unknown dependency FND-999",
        "gate G-02 is PENDING",
    ]
    assert tasks.blockers(t["FND-003"], t, g) == [
        "gate G-09 is missing",
        "explicitly blocked - see task file",
    ]


def test_gate_ok() -> None:
    gates = {"G-01": "approved (b)", "G-02": "PENDING"}
    assert tasks.gate_ok(None, gates)
    assert tasks.gate_ok("G-01", gates)
    assert not tasks.gate_ok("G-02", gates)
    assert not tasks.gate_ok("G-03", gates)


def test_eligible_orders_by_phase_then_unblocked_work_then_id(write_task: WriteTask) -> None:
    write_task("FND-009", phase="1")  # unblocks nothing
    write_task("FND-008", phase="1")  # unblocks nothing, lower id
    write_task("FND-007", phase="1")  # unblocks 2 (transitively)
    write_task("FND-001", phase="2")  # later phase, despite the lowest id
    write_task("DAT-001", phase="3", depends_on="[FND-007]")
    write_task("DAT-002", phase="3", depends_on="[DAT-001]")
    write_task("FND-010", phase="1", status="done")  # not todo
    t, g = _load()
    assert [x.id for x in tasks.eligible(t, g)] == ["FND-007", "FND-008", "FND-009", "FND-001"]
    assert tasks.transitive_dependents("FND-007", t) == 2


# ------------------------------------------------------------------ validate / spec standard


def test_validate_clean_repo(write_task: WriteTask, capsys: pytest.CaptureFixture[str]) -> None:
    write_task("FND-001", gate="G-01")
    t, g = _load()
    assert tasks.cmd_validate(t, g) == 0
    assert capsys.readouterr().out.strip() == "1 tasks, 0 errors, 0 warnings (-w to list)"


def test_validate_detects_cycles(write_task: WriteTask, capsys: pytest.CaptureFixture[str]) -> None:
    write_task("FND-001", depends_on="[FND-003]")
    write_task("FND-002", depends_on="[FND-001]")
    write_task("FND-003", depends_on="[FND-002]")
    t, g = _load()
    assert tasks.cmd_validate(t, g) == 1
    out = capsys.readouterr().out
    assert "ERROR cycle: FND-001 -> FND-003 -> FND-002 -> FND-001" in out


def test_validate_returns_nonzero_on_errors(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("fnd-1", status="bogus", autonomy="yolo", size="L", gate="G-77")
    write_task("FND-002", depends_on="[FND-404]", title=None)
    (tasks.TASK_DIR / "FND-002-slug.md").rename(tasks.TASK_DIR / "WRONG-name.md")
    t, g = _load()
    assert tasks.cmd_validate(t, g) == 1
    out = capsys.readouterr().out
    for expected in (
        "fnd-1: bad id format",
        "fnd-1: bad status bogus",
        "fnd-1: bad autonomy",
        "fnd-1: size must be S or M",
        "fnd-1: unknown gate G-77",
        "FND-002: missing 'title'",
        "FND-002: filename must start with the id",
        "FND-002: unknown dependency FND-404",
    ):
        assert expected in out


def test_validate_lists_warnings_with_w(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("FND-001", body="## Objective\nx\n\n## Acceptance criteria\n- [ ] AC1: no verify\n")
    t, g = _load()
    assert tasks.cmd_validate(t, g, verbose_warnings=True) == 0
    out = capsys.readouterr().out
    assert "WARN  FND-001: missing section '## Test requirements'" in out
    assert "WARN  FND-001: AC1 has no 'Verify:' line" in out
    assert "0 errors, 3 warnings" in out


def test_spec_issues_are_errors_at_review(write_task: WriteTask) -> None:
    write_task(
        "FND-001",
        status="review",
        body="## Objective\nx\n\n## Acceptance criteria\n- [ ] AC1: no verify\n",
    )
    errors, warnings = tasks.spec_issues(_load()[0]["FND-001"])
    assert warnings == []
    assert "FND-001: AC1 has no 'Verify:' line" in errors
    assert "FND-001: missing section '## Evidence'" in errors


def test_spec_issues_ready_task_without_criteria(write_task: WriteTask) -> None:
    write_task("FND-001", body="## Objective\nx\n\n## Acceptance criteria\nTBD\n")
    errors, _ = tasks.spec_issues(_load()[0]["FND-001"])
    assert errors == ["FND-001: ready task has no '- [ ] ACn:' criteria"]


def test_ready_task_without_criteria_section_fails_validate(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("FND-001", body="## Objective\nx\n")
    t, g = _load()
    assert tasks.cmd_validate(t, g) == 1
    assert "FND-001: ready task needs '## Acceptance criteria'" in capsys.readouterr().out


@pytest.mark.parametrize(("status", "ready"), [("cancelled", "true"), ("todo", "false")])
def test_spec_issues_skip_cancelled_and_placeholders(
    write_task: WriteTask, status: str, ready: str
) -> None:
    write_task("FND-001", body="placeholder\n", status=status, ready=ready)
    assert tasks.spec_issues(_load()[0]["FND-001"]) == ([], [])


# ------------------------------------------------------------------ claim


def test_claim_sets_status_and_assignee(write_task: WriteTask) -> None:
    path = write_task("FND-001")
    t, g = _load()
    assert tasks.cmd_claim(t, g, "FND-001", "alice") == 0
    reparsed = tasks.parse_task(path)
    assert reparsed.status == "in_progress"
    assert reparsed.meta["assignee"] == "alice"


def test_claim_adds_missing_fields(write_task: WriteTask) -> None:
    path = write_task("FND-001", assignee=None)
    t, g = _load()
    assert tasks.cmd_claim(t, g, "FND-001", "bob") == 0
    assert tasks.parse_task(path).meta["assignee"] == "bob"


def test_claim_conflict_is_refused(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_task("FND-001", status="in_progress", assignee="alice")
    before = path.read_text(encoding="utf-8")
    t, g = _load()
    assert tasks.cmd_claim(t, g, "FND-001", "bob") == 1
    assert "FND-001 already claimed by alice" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == before
    # the same claimant may re-claim (resume) its own task
    assert tasks.cmd_claim(t, g, "FND-001", "alice") == 0


def test_claim_blocked_task_is_refused(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("FND-001")
    write_task("FND-002", depends_on="[FND-001]")
    t, g = _load()
    assert tasks.cmd_claim(t, g, "FND-002", "alice") == 1
    assert "cannot claim: waits on FND-001 (todo)" in capsys.readouterr().out


# ------------------------------------------------------------------ done

EVIDENCE = (
    "| AC | Type | Reference | Result |\n|---|---|---|---|\n| AC1 | command | `echo ok` | ok |"
)


def test_done_refuses_without_evidence(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_task("FND-001", status="in_progress")
    before = path.read_text(encoding="utf-8")
    t, g = _load()
    assert tasks.cmd_done(t, g, "FND-001") == 1
    out = capsys.readouterr().out
    assert "cannot mark done" in out
    assert "FND-001: done but no Evidence row for AC1" in out
    assert path.read_text(encoding="utf-8") == before
    assert not tasks.BOARD_FILE.exists()


def test_done_reports_newly_unblocked_and_writes_board(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_task("FND-001", status="in_progress", evidence=EVIDENCE)
    write_task("FND-002", depends_on="[FND-001]")
    write_task("FND-003", depends_on="[FND-001]", gate="G-02")  # still gated
    write_task("FND-004")  # already eligible: not "newly" unblocked
    t, g = _load()
    assert tasks.cmd_done(t, g, "FND-001") == 0
    out = capsys.readouterr().out
    assert "FND-001 done. Newly unblocked: FND-002\n" in out
    done = tasks.parse_task(path)
    assert done.status == "done"
    assert str(done.meta["completed"]).count("-") == 2  # ISO date
    assert "| [FND-001](FND-001-slug.md) | Title FND-001 | done |" in tasks.BOARD_FILE.read_text(
        encoding="utf-8"
    )


def test_done_with_nothing_unblocked(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("FND-001", status="in_progress", evidence=EVIDENCE)
    t, g = _load()
    assert tasks.cmd_done(t, g, "FND-001") == 0
    assert "Newly unblocked: none" in capsys.readouterr().out


# ------------------------------------------------------------------ board


def _make_board_tasks(write_task: WriteTask, order: list[str]) -> None:
    specs = {
        "DAT-002": {"phase": "2", "depends_on": "[FND-001]"},
        "FND-002": {"phase": "1", "gate": "G-02"},
        "FND-001": {"phase": "1", "status": "done"},
        "DAT-001": {"phase": "2", "ready": "false"},
    }
    for tid in order:
        write_task(tid, **specs[tid])


def test_board_is_deterministic(write_task: WriteTask) -> None:
    _make_board_tasks(write_task, ["DAT-002", "FND-002", "FND-001", "DAT-001"])
    t, g = _load()
    tasks.cmd_board(t, g)
    first = tasks.BOARD_FILE.read_bytes()
    for p in tasks.TASK_DIR.glob("*-slug.md"):
        p.unlink()
    _make_board_tasks(write_task, ["FND-001", "DAT-001", "FND-002", "DAT-002"])
    t, g = _load()
    # reversed dict insertion order must not change the output either
    tasks.cmd_board(dict(reversed(list(t.items()))), g)
    assert tasks.BOARD_FILE.read_bytes() == first


def test_board_orders_phases_and_ids(write_task: WriteTask) -> None:
    _make_board_tasks(write_task, ["DAT-002", "FND-002", "FND-001", "DAT-001"])
    t, g = _load()
    assert tasks.cmd_board(t, g) == 0
    lines = tasks.BOARD_FILE.read_text(encoding="utf-8").splitlines()
    rows = [line for line in lines if line.startswith(("## Phase", "| ["))]
    assert [r.split("]")[0] for r in rows] == [
        "## Phase 1",
        "| [FND-001",
        "| [FND-002",
        "## Phase 2",
        "| [DAT-001",
        "| [DAT-002",
    ]
    fnd001 = next(r for r in rows if r.startswith("| [FND-001"))
    assert fnd001.endswith("|  |")  # done tasks show no blockers
    assert "gate G-02 is PENDING" in next(r for r in rows if r.startswith("| [FND-002"))


# ------------------------------------------------------------------ read-only commands + main


def test_next_status_show_gates(write_task: WriteTask, capsys: pytest.CaptureFixture[str]) -> None:
    write_task("FND-001", status="in_progress", assignee="alice")
    write_task("FND-002")
    write_task("FND-003", depends_on="[FND-002]")
    t, g = _load()
    assert tasks.cmd_status(t, g) == 0
    out = capsys.readouterr().out
    assert "Tasks: in_progress=1, todo=2" in out
    assert "IN PROGRESS FND-001 (alice): Title FND-001" in out
    assert "Pending gates (1): G-02" in out
    assert "FND-002  [P1 S auto]  Title FND-002  (unblocks 1)" in out
    assert tasks.cmd_show(t, g, "FND-003") == 0
    out = capsys.readouterr().out
    assert "blockers: waits on FND-002 (todo)" in out
    assert "dependents: none" in out
    assert tasks.cmd_show(t, g, "NOPE-001") == 1
    assert "unknown task NOPE-001" in capsys.readouterr().out


def test_next_without_eligible_lists_pending_gates(
    write_task: WriteTask, capsys: pytest.CaptureFixture[str]
) -> None:
    write_task("FND-001", gate="G-02")
    t, g = _load()
    assert tasks.cmd_next(t, g, 3) == 0
    assert (
        capsys.readouterr().out
        == "No eligible tasks. Pending gates / blocked work:\nG-02: PENDING\n"
    )


@pytest.mark.parametrize(
    "case",
    [
        (["validate"], 0, "2 tasks, 0 errors"),
        (["validate", "-w"], 0, "0 warnings"),
        (["next", "-n", "1"], 0, "FND-001"),
        (["show", "FND-002"], 0, "blockers: waits on FND-001"),
        (["why", "FND-002"], 0, "blockers: waits on FND-001"),
        (["board"], 0, "wrote"),
        (["status"], 0, "Tasks: todo=2"),
        (["gates"], 0, "G-02: PENDING"),
        (["claim", "FND-001", "--by", "carol"], 0, "claimed FND-001"),
        (["done", "FND-001"], 1, "cannot mark done"),
    ],
)
def test_main_dispatch(
    write_task: WriteTask,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    case: tuple[list[str], int, str],
) -> None:
    argv, code, expected = case
    write_task("FND-001")
    write_task("FND-002", depends_on="[FND-001]")
    monkeypatch.setattr(sys, "argv", ["tasks.py", *argv])
    assert tasks.main() == code
    assert expected in capsys.readouterr().out


# ------------------------------------------------------------------ just check wiring


def test_validate_is_wired_into_just_check() -> None:
    justfile = (Path(__file__).resolve().parents[2] / "justfile").read_text(encoding="utf-8")
    check = justfile.split("\ncheck:", 1)[1].split("\n\n", 1)[0]
    assert "python tools/tasks.py validate" in check
    assert "ci-local: check" in justfile


# ------------------------------------------------------------------ user stories (IMP-006)
STORIES = (
    "\n## User stories and edge cases\n"
    "| Persona | Story | Edge cases |\n|---|---|---|\n| a | b | c |\n"
)


@pytest.mark.parametrize("component", ["web", "api"])
def test_user_facing_task_without_stories_warns_then_errors_at_review(
    write_task: WriteTask, component: str
) -> None:
    write_task("WEB-001", component=component)
    _, warnings = tasks.spec_issues(_load()[0]["WEB-001"])
    assert "WEB-001: user-facing task has no '## User stories and edge cases'" in warnings
    write_task("WEB-001", component=component, status="review")
    errors, _ = tasks.spec_issues(_load()[0]["WEB-001"])
    assert "WEB-001: user-facing task has no '## User stories and edge cases'" in errors


def test_user_facing_task_with_stories_passes(write_task: WriteTask) -> None:
    body = GOOD_BODY.format(id="WEB-001", evidence="") + STORIES
    write_task("WEB-001", body=body, component="web")
    assert tasks.spec_issues(_load()[0]["WEB-001"]) == ([], [])


@pytest.mark.parametrize(("component", "status"), [("ingest", "review"), ("web", "done")])
def test_stories_not_required_for_internal_or_finished_tasks(
    write_task: WriteTask, component: str, status: str
) -> None:
    write_task("WEB-001", component=component, status=status, evidence="| AC1 | test | t | pass |")
    errors, warnings = tasks.spec_issues(_load()[0]["WEB-001"])
    assert not [m for m in errors + warnings if "User stories" in m]
