#!/usr/bin/env python3
"""Environment doctor: reports which tools, logins and secrets are set up.

Never prints secret values, only whether they are present. Stdlib only.
Usage: python tools/doctor.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
REQUIRED_ENV = {
    "YAHOO_CLIENT_ID": "Yahoo app (owner step 3)",
    "YAHOO_CLIENT_SECRET": "Yahoo app (owner step 3)",
    "TELEGRAM_BOT_TOKEN": "Telegram bot (owner step 4)",
}
OPTIONAL_ENV = {"ANTHROPIC_API_KEY": "Claude API, needed later for NL questions (D-36)"}


def _run(cmd: list[str]) -> tuple[bool, str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return False, "not installed / not on PATH"
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    out = (p.stdout + p.stderr).strip().splitlines()
    first = out[0] if out else ""
    ok = p.returncode == 0 and not first.lower().startswith(("error", "warning: no"))
    return ok, first


def _env_keys() -> set[str]:
    keys = {k for k in os.environ if os.environ[k]}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#") and v.strip():
                keys.add(k.strip())
    return keys


def main() -> int:
    ok_all = True
    print("== Tools")
    for name, cmd in [
        ("uv", ["uv", "--version"]),
        ("just", ["just", "--version"]),
        ("gh", ["gh", "--version"]),
        ("gcloud", ["gcloud", "--version"]),
        ("terraform", ["terraform", "--version"]),
        ("docker engine", ["docker", "info", "--format", "{{.ServerVersion}}"]),
    ]:
        ok, msg = _run(cmd)
        ok_all &= ok
        print(f"  [{'x' if ok else ' '}] {name}: {msg if ok else 'MISSING - ' + msg}")
    print("== Logins")
    ok, _ = _run(["gh", "auth", "status"])
    ok_all &= ok
    print(f"  [{'x' if ok else ' '}] GitHub (gh auth login)")
    ok, msg = _run(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
    ok = ok and "@" in msg
    ok_all &= ok
    print(f"  [{'x' if ok else ' '}] Google Cloud user login (gcloud auth login)")
    adc = (
        Path(os.environ.get("APPDATA", Path.home() / ".config"))
        / "gcloud"
        / "application_default_credentials.json"
    )
    if not adc.exists():
        adc = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    ok_all &= adc.exists()
    mark = "x" if adc.exists() else " "
    print(f"  [{mark}] Google Cloud app credentials (gcloud auth application-default login)")
    print("== Secrets in .env (values never shown)")
    keys = _env_keys()
    for k, why in REQUIRED_ENV.items():
        ok_all &= k in keys
        print(f"  [{'x' if k in keys else ' '}] {k}: {why}")
    tfvars = ROOT / "infra" / "terraform" / "bootstrap" / "terraform.tfvars"
    has_billing = tfvars.exists() and "billing_account" in tfvars.read_text(encoding="utf-8")
    ok_all &= has_billing
    mark = "x" if has_billing else " "
    print(f"  [{mark}] GCP billing account ID in infra/terraform/bootstrap/terraform.tfvars")
    for k, why in OPTIONAL_ENV.items():
        print(f"  [{'x' if k in keys else '-'}] {k}: {why} (optional for now)")
    print(
        "\nAll set."
        if ok_all
        else "\nSome items still need the owner - see docs/runbooks/owner-setup.md"
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
