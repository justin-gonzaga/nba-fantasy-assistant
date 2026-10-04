"""Guards the pre-commit hooks and line-ending policy (security standard §1, FND-005)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_HOOKS = {
    "ruff-format",
    "ruff-check",
    "gitleaks",
    "end-of-file-fixer",
    "trailing-whitespace",
    "check-yaml",
    "check-added-large-files",
    "nbstripout",
}


def _hook_ids() -> set[str]:
    text = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^\s*-\s*id:\s*([\w-]+)", text, re.M))


def test_precommit_runs_required_hooks() -> None:
    assert _hook_ids() >= REQUIRED_HOOKS


def test_precommit_is_a_dev_dependency() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dev = pyproject.split("[dependency-groups]", 1)[1].split("]", 1)[0]
    assert '"pre-commit' in dev


def test_setup_installs_the_git_hook() -> None:
    justfile = (ROOT / "justfile").read_text(encoding="utf-8")
    setup = justfile.split("\nsetup:", 1)[1].split("\n\n", 1)[0]
    assert "pre-commit install" in setup


def test_gitattributes_rules() -> None:
    rules = {
        tuple(line.split(None, 1))
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert ("*", "text=auto eol=lf") in rules
    for pattern in ("*.ps1", "*.bat", "*.cmd"):
        assert (pattern, "text eol=crlf") in rules
    for pattern in ("*.pdf", "*.png", "*.zip"):
        assert (pattern, "binary") in rules
