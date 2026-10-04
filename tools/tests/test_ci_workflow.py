"""CI ordering guarantees (WEB-016 AC7): the site never goes live ahead of the API it calls."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]

CI = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"


def test_hosting_waits_for_the_api_deploy_on_main() -> None:
    hosting = yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]["hosting"]
    assert "deploy-api" in hosting["needs"]
    cond = " ".join(hosting["if"].split())
    assert cond.startswith("always()")
    # On main the API deploy must succeed; a skipped one (e.g. a failed image) doesn't count.
    assert "needs.deploy-api.result == 'success'" in cond
    assert "needs.deploy-api.result == 'skipped'" not in cond
    assert "github.event_name == 'pull_request'" in cond  # PR previews use sample data, no API
