"""The kernel stays domain-neutral: no project terms in its source or tests (GEN-003 AC1)."""

import re
from pathlib import Path

import dikit

TERMS = re.compile(
    r"nba|yahoo|fantasy|basketball|player|league|draft|roster|telegram|wnba",
    re.IGNORECASE,
)
SOURCE = Path(dikit.__file__).parent
TESTS = Path(__file__).parent


def _hits(root: Path) -> list[str]:
    return [
        f"{p.relative_to(root)}:{n}: {line.strip()}"
        for p in sorted(root.rglob("*.py"))
        if p.resolve() != Path(__file__).resolve()
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if TERMS.search(line)
    ]


def test_kernel_source_has_no_project_terms() -> None:
    assert _hits(SOURCE) == []


def test_kernel_tests_have_no_project_terms() -> None:
    assert _hits(TESTS) == []
