"""Post-apply IAM checks via Policy Troubleshooter (INFRA-002 AC5).

Asks Google whether each workload SA has a permission, without acting as that SA.
Deny checks prove least privilege; each principal also has a positive control.

    python tools/iam_negative_tests.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

PREFIX = "nbafa-hdfo"


def _sa(workload: str, env: str) -> str:
    return f"{workload}-sa@{PREFIX}-{env}.iam.gserviceaccount.com"


def _bucket(env: str, purpose: str = "raw") -> str:
    return f"//storage.googleapis.com/projects/_/buckets/{PREFIX}-{env}-{purpose}"


def _dataset(env: str, dataset: str) -> str:
    return f"//bigquery.googleapis.com/projects/{PREFIX}-{env}/datasets/{dataset}"


@dataclass(frozen=True)
class Check:
    principal: str
    resource: str
    permission: str
    expect_granted: bool


CHECKS: list[Check] = [
    # ingest: create + read raw, never delete (immutable bronze)
    Check(_sa("ingest", "prod"), _bucket("prod"), "storage.objects.create", True),
    Check(_sa("ingest", "prod"), _bucket("prod"), "storage.objects.delete", False),
    Check(_sa("ingest", "dev"), _bucket("dev"), "storage.objects.delete", False),
    # dev SAs read prod raw (I3 A) but cannot write it
    Check(_sa("ingest", "dev"), _bucket("prod"), "storage.objects.get", True),
    Check(_sa("ingest", "dev"), _bucket("prod"), "storage.objects.create", False),
    # api: read serving data, write nothing
    Check(_sa("api", "prod"), _dataset("prod", "marts"), "bigquery.tables.getData", True),
    Check(_sa("api", "prod"), _dataset("prod", "marts"), "bigquery.tables.updateData", False),
    Check(_sa("api", "prod"), _dataset("prod", "raw"), "bigquery.tables.getData", False),
    # transform: edits its layers, only reads raw
    Check(
        _sa("transform", "prod"), _dataset("prod", "staging"), "bigquery.tables.updateData", True
    ),
    Check(_sa("transform", "prod"), _dataset("prod", "raw"), "bigquery.tables.updateData", False),
]


def access_granted(reply: str) -> bool:
    state = json.loads(reply).get("overallAccessState", "")
    if state == "CAN_ACCESS":
        return True
    if state == "CANNOT_ACCESS":
        return False
    msg = f"inconclusive troubleshooter state: {state or 'UNKNOWN'}"
    raise ValueError(msg)


def gcloud_runner(check: Check) -> str:  # pragma: no cover - needs GCP
    gcloud = shutil.which("gcloud") or "gcloud"
    return subprocess.run(
        [
            gcloud,
            "policy-intelligence",
            "troubleshoot-policy",
            "iam",
            check.resource,
            f"--principal-email={check.principal}",
            f"--permission={check.permission}",
            f"--project={PREFIX}-dev",
            "--format=json",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def run_checks(checks: list[Check], runner: Callable[[Check], str]) -> list[tuple[Check, bool]]:
    return [(c, access_granted(runner(c)) == c.expect_granted) for c in checks]


def main(runner: Callable[[Check], str] = gcloud_runner) -> int:
    results = run_checks(CHECKS, runner)
    for c, ok in results:
        want = "allow" if c.expect_granted else "deny"
        who = c.principal.split(".iam")[0]
        print(f"{'PASS' if ok else 'FAIL'}  {want:5}  {who}  {c.permission}  {c.resource}")
    failed = sum(not ok for _c, ok in results)
    print(f"{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
