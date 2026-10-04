import json

import pytest

from tools.iam_negative_tests import CHECKS, Check, access_granted, main, run_checks


def _reply(state: str) -> str:
    return json.dumps({"overallAccessState": state})


def test_access_granted_parses_troubleshooter_states() -> None:
    assert access_granted(_reply("CAN_ACCESS")) is True
    assert access_granted(_reply("CANNOT_ACCESS")) is False


def test_access_granted_rejects_unknown_state() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        access_granted(_reply("UNKNOWN_INFO"))


def test_checks_cover_the_acceptance_criteria() -> None:
    denied = {(c.principal.split("@")[0], c.permission) for c in CHECKS if not c.expect_granted}
    assert ("ingest-sa", "storage.objects.delete") in denied
    assert ("api-sa", "bigquery.tables.updateData") in denied
    assert ("transform-sa", "bigquery.tables.updateData") in denied
    # every deny check has at least one positive control for the same principal
    for principal in {c.principal for c in CHECKS if not c.expect_granted}:
        assert any(c.principal == principal and c.expect_granted for c in CHECKS)


def test_run_checks_reports_mismatches() -> None:
    checks = [
        Check("ingest-sa@p.iam.gserviceaccount.com", "//r", "storage.objects.delete", False),
        Check("ingest-sa@p.iam.gserviceaccount.com", "//r", "storage.objects.create", True),
    ]
    all_granted = run_checks(checks, lambda _c: _reply("CAN_ACCESS"))
    assert [ok for _c, ok in all_granted] == [False, True]


def test_main_exit_code(capsys: pytest.CaptureFixture[str]) -> None:
    def expected(c: Check) -> str:
        return _reply("CAN_ACCESS" if c.expect_granted else "CANNOT_ACCESS")

    assert main(runner=expected) == 0
    assert main(runner=lambda _c: _reply("CAN_ACCESS")) == 1
    assert "FAIL" in capsys.readouterr().out
