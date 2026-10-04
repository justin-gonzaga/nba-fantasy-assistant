"""Check that every tracked file belongs to a layer in platform-manifest.yaml (GEN-002, D-58).

Usage: python tools/manifest_check.py [--summary]
Exit 1 when a tracked file matches no section. Stdlib + a tiny YAML reader (the manifest is a
flat mapping of lists), so it runs before the uv environment exists, like tools/tasks.py.
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("harness", "platform", "mixed", "domain")


def load(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {s: [] for s in ORDER}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current = line[:-1] if line[:-1] in sections else None
        elif current and line.strip().startswith("- "):
            sections[current].append(line.strip()[2:].strip())
    return sections


def layer(path: str, sections: dict[str, list[str]]) -> str | None:
    for name in ORDER:
        if any(fnmatch.fnmatch(path, pat) for pat in sections[name]):
            return name
    return None


def tracked(root: Path = ROOT) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def main(argv: list[str]) -> int:
    sections = load(ROOT / "platform-manifest.yaml")
    files = tracked()
    unclassified = [f for f in files if layer(f, sections) is None]
    if "--summary" in argv:
        counts = Counter(layer(f, sections) or "UNCLASSIFIED" for f in files)
        for name in (*ORDER, "UNCLASSIFIED"):
            print(f"{name}: {counts.get(name, 0)}")
    for f in unclassified:
        print(f"unclassified: {f}")
    return 1 if unclassified else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
