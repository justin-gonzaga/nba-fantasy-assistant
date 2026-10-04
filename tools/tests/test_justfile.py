"""Guards the project command surface (devops standard §1, FND-003)."""

import re
from pathlib import Path

JUSTFILE = Path(__file__).resolve().parents[2] / "justfile"
REQUIRED = {"setup", "check", "ci-local", "test", "status", "task", "doctor"}


def _recipes() -> dict[str, list[str]]:
    recipes: dict[str, list[str]] = {}
    current: str | None = None
    for line in JUSTFILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z][\w-]*)(?:\s+[^:]*)?:", line)
        if m and not line.startswith(" "):
            current = m.group(1)
            recipes[current] = []
        elif current and line.startswith("    "):
            recipes[current].append(line.strip())
    return recipes


def test_required_recipes_exist() -> None:
    assert set(_recipes()) >= REQUIRED


def test_recipes_are_shell_portable() -> None:
    # Recipes must behave the same under PowerShell 5.1 and sh: no && / || chaining, no backslashes.
    for name, body in _recipes().items():
        for cmd in body:
            assert "&&" not in cmd, f"{name}: {cmd}"
            assert "||" not in cmd, f"{name}: {cmd}"
            assert "\\" not in cmd, f"{name}: {cmd}"


def test_ci_local_enforces_coverage() -> None:
    assert any("--cov" in cmd for cmd in _recipes()["ci-local"])


def test_dbt_recipe_uses_the_warehouse_group_and_repo_profiles() -> None:
    body = " ".join(_recipes()["dbt"])
    assert "--group warehouse" in body
    assert "--project-dir warehouse" in body
    assert "--profiles-dir warehouse" in body
