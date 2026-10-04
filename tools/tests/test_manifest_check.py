import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "manifest_check", Path(__file__).parents[1] / "manifest_check.py"
)
assert _SPEC is not None
assert _SPEC.loader is not None
mc = importlib.util.module_from_spec(_SPEC)
sys.modules["manifest_check"] = mc
_SPEC.loader.exec_module(mc)


def test_load_reads_sections_and_ignores_comments(tmp_path: Path) -> None:
    f = tmp_path / "m.yaml"
    f.write_text(
        "version: 1\nharness:\n  - CLAUDE.md  # the index\nplatform:\n  - packages/core/*\n"
        "mixed:\ndomain:\n  - apps/*\n",
        encoding="utf-8",
    )
    s = mc.load(f)
    assert s["harness"] == ["CLAUDE.md"]
    assert s["platform"] == ["packages/core/*"]
    assert s["mixed"] == []


def test_first_matching_section_wins() -> None:
    s = {
        "harness": [],
        "platform": ["packages/core/src/x.py"],
        "mixed": [],
        "domain": ["packages/*"],
    }
    assert mc.layer("packages/core/src/x.py", s) == "platform"
    assert mc.layer("packages/models/y.py", s) == "domain"
    assert mc.layer("elsewhere.txt", s) is None


def test_every_tracked_file_in_this_repo_is_classified() -> None:
    sections = mc.load(mc.ROOT / "platform-manifest.yaml")
    assert [f for f in mc.tracked() if mc.layer(f, sections) is None] == []
