#!/usr/bin/env python3
"""One-time Yahoo OAuth2 consent + token refresh check (DISC-001 spike tooling). Stdlib only.

Owner runs (in their own terminal, never in chat):
    python tools/yahoo_login.py          # consent: opens Yahoo; paste the redirected address back
    python tools/yahoo_login.py --check  # refresh the token and list your NBA leagues

Secrets are read from .env and the token is written to secrets/yahoo_token.json (both gitignored).
Nothing secret is ever printed.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from getpass import getpass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"  # noqa: S105 - endpoint URL, not a secret
API = "https://fantasysports.yahooapis.com/fantasy/v2"
REDIRECT_URI = "https://localhost:8080"
TOKEN_FILE = ROOT / "secrets" / "yahoo_token.json"
USER_AGENT = "nba-fantasy-assistant/0.1 (personal, non-commercial)"


def parse_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.strip().startswith("#") and value.strip():
                env[key.strip()] = value.strip()
    return env


def authorize_url(client_id: str) -> str:
    q = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "language": "en-us",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(q)}"


def extract_code(pasted: str) -> str:
    text = pasted.strip()
    if text.startswith("http"):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(text).query).get("code", [""])[0]
    else:
        code = text
    if not code:
        raise ValueError("no authorization code found in what was pasted")
    return code


def _token_request(client_id: str, secret: str, form: dict[str, str]) -> dict[str, Any]:
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(form).encode(),
        headers={
            "Authorization": f"Basic {basic}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        data: dict[str, Any] = json.loads(r.read())
    data["obtained_at"] = int(time.time())
    return data


def _save(token: dict[str, Any]) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token), encoding="utf-8")
    with contextlib.suppress(OSError):
        TOKEN_FILE.chmod(0o600)


def _api(path: str, access_token: str) -> dict[str, Any]:
    req = urllib.request.Request(  # noqa: S310 - fixed https endpoint
        f"{API}/{path}{'&' if '?' in path else '?'}format=json",
        headers={"Authorization": f"Bearer {access_token}", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        result: dict[str, Any] = json.loads(r.read())
    return result


def _list_leagues(access_token: str) -> list[dict[str, str]]:
    data = _api("users;use_login=1/games;game_codes=nba/leagues", access_token)
    leagues: list[dict[str, str]] = []
    users = data["fantasy_content"]["users"]
    games = users["0"]["user"][1]["games"]
    for gk, g in games.items():
        if gk == "count":
            continue
        game = g["game"]
        season = game[0].get("season", "?")
        lg = game[1].get("leagues", {}) if len(game) > 1 else {}
        for lk, entry in lg.items():
            if lk == "count":
                continue
            meta = entry["league"][0]
            leagues.append(
                {
                    "season": str(season),
                    "league_key": meta["league_key"],
                    "name": meta["name"],
                    "scoring_type": meta.get("scoring_type", "?"),
                    "num_teams": str(meta.get("num_teams", "?")),
                }
            )
    return leagues


def consent(env: dict[str, str]) -> int:
    url = authorize_url(env["YAHOO_CLIENT_ID"])
    print("1) A Yahoo page will open. Sign in with the account in your league and click Agree.")
    print("2) The browser then goes to https://localhost:8080/?code=... and shows an error page.")
    print("   That's expected.")
    print("3) Copy the WHOLE address from the address bar and paste it below (input is hidden).\n")
    print(f"If the browser doesn't open, visit:\n{url}\n")
    webbrowser.open(url)
    code = extract_code(getpass("Paste the address (or just the code): "))
    token = _token_request(
        env["YAHOO_CLIENT_ID"],
        env["YAHOO_CLIENT_SECRET"],
        {"grant_type": "authorization_code", "redirect_uri": REDIRECT_URI, "code": code},
    )
    _save(token)
    print(f"\n✓ Token saved to {TOKEN_FILE.relative_to(ROOT)} (gitignored).")
    print(f"  Access token lifetime: {token.get('expires_in')} s.")
    return check(env)


def check(env: dict[str, str]) -> int:
    if not TOKEN_FILE.exists():
        print("No token yet. Run `python tools/yahoo_login.py` first.")
        return 1
    old = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    token = _token_request(
        env["YAHOO_CLIENT_ID"],
        env["YAHOO_CLIENT_SECRET"],
        {
            "grant_type": "refresh_token",
            "redirect_uri": REDIRECT_URI,
            "refresh_token": old["refresh_token"],
        },
    )
    token.setdefault("refresh_token", old["refresh_token"])
    _save(token)
    print(f"✓ Refresh works (new access token lifetime {token.get('expires_in')} s).")
    leagues = _list_leagues(token["access_token"])
    print(f"✓ Found {len(leagues)} NBA league(s) on this Yahoo account:")
    for lg in leagues:
        detail = f"scoring: {lg['scoring_type']}, teams: {lg['num_teams']}"
        print(f"  - {lg['season']}  {lg['league_key']}  {lg['name']}  ({detail})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true", help="refresh the token and list NBA leagues")
    ap.add_argument("--env", type=Path, default=ROOT / ".env", help="path to .env")
    a = ap.parse_args()
    env = parse_env(a.env)
    missing = [k for k in ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET") if k not in env]
    if missing:
        print(f"Missing in {a.env}: {', '.join(missing)}. See docs/runbooks/owner-setup.md step 3.")
        return 1
    try:
        return check(env) if a.check else consent(env)
    except urllib.error.HTTPError as e:
        print(f"Yahoo returned HTTP {e.code}: {e.reason}.")
        detail = e.read().decode("utf-8", "replace")[:400]  # API error text, never the token
        print(f"Yahoo said: {detail}")
        print("Re-run the consent step if the refresh token was revoked.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
