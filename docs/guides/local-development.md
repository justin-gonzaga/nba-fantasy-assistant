# Local Development Guide

How to set up a machine to work on this project, from scratch. Every command here has been run on the reference
machine (Windows 11, 2026-09-25). Later sections are added as the setup grows: repo bootstrap, cloud access, secrets.

## 1. Prerequisites

### 1.1 Tools and why each is needed
| Tool | Version tested | Purpose | Decision |
|---|---|---|---|
| Git | 2.50 | version control | — |
| Python | 3.13 | the main language (uv manages it for the project) | F1, F2 |
| uv | 0.12.18 | Python packages, environments, Python versions | F3 |
| just | 1.58.0 | the project command runner (`just check`, `just ship`, …) | F4 |
| GitHub CLI (`gh`) | 2.101.0 | PRs, CI status, and merges from the terminal | F6 |
| Google Cloud SDK (`gcloud`) | 586.0.0 | GCP auth + BigQuery/GCS/Cloud Run tooling | I1–I6 |
| Terraform | 1.16.2 | infrastructure as code | I1 |
| Docker Desktop (+ WSL2 on Windows) | latest | container image builds, local parity | F5 |

### 1.2 Windows 11 (reference setup)
Run in **PowerShell**. winget ships with Windows 11.

```powershell
# Python packaging/env manager
winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements

# GitHub CLI and Terraform
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
winget install --id Hashicorp.Terraform -e --accept-package-agreements --accept-source-agreements

# Google Cloud SDK (the installer asks for administrator approval)
winget install --id Google.CloudSDK -e --accept-package-agreements --accept-source-agreements
```

**Open a new PowerShell window** so the updated PATH applies, then:

```powershell
# just, installed as a uv-managed tool, and uv's tool directory added to PATH
uv tool install rust-just
uv tool update-shell        # then open another new window
```

**Docker Desktop** needs admin rights and a sign-in, so do it by hand:
1. Run `wsl --install` in an elevated PowerShell. It installs WSL2 + Ubuntu, and may ask for a restart.
2. Install Docker Desktop from docker.com, start it, and sign in.

### 1.3 macOS / Linux (equivalents, untested on the reference machine)
```bash
# macOS (Homebrew)
brew install uv just gh terraform
brew install --cask google-cloud-sdk docker
# Linux: uv via `curl -LsSf https://astral.sh/uv/install.sh | sh`, then `uv tool install rust-just`;
# gh, terraform and gcloud from their official apt/yum repositories; Docker Engine from docs.docker.com.
```

### 1.4 Verify (new shell)
```powershell
uv --version; just --version; gh --version; gcloud --version; terraform --version
uv python find 3.13          # prints a Python 3.13 path
docker run --rm hello-world  # prints "Hello from Docker!"
```

## 2. Accounts and sign-ins (one-time, done by a human)
**Step-by-step checklist: [`docs/runbooks/owner-setup.md`](../runbooks/owner-setup.md)**. Check progress with `python tools/doctor.py`, which never prints secret values.

Each step is done when the task that needs it comes up. Claude never handles credentials.

| Step | Command / action | Needed by |
|---|---|---|
| GitHub | `gh auth login` (browser) | FND-006 (repo + CI) |
| Google Cloud | create a billing account in the console; `gcloud auth login` + `gcloud auth application-default login` (browser) | INFRA-001 |
| Yahoo developer app | register an app with *Fantasy Sports: Read* (steps in `docs/runbooks/yahoo-auth.md`, coming with DATA-003); then `just yahoo-login` | DATA-003 |
| Telegram bot | create a bot with @BotFather; put the token in Secret Manager (steps with FND-013) | FND-013 |

## 3. Get the code and run the checks
_Available once FND-002/FND-003 land._
```powershell
git clone <repo-url>; cd nba-fantasy-assistant
just setup      # installs the Python version + dependencies (uv sync) and pre-commit hooks
just doctor     # tool versions + which configuration is present (never prints secrets)
just check      # fast lint, types, tests
```

## 4. Working with Claude Code
- Project instructions are in `CLAUDE.md`; skills (`/status`, `/next`, `/work-task`, `/new-task`, `/gate`, `/checkpoint`, `/adr`) are in `.claude/skills/`.
- **From your phone**: run `/remote-control` (or `/rc`) in a session on the laptop, then open it in the Claude app or at claude.ai/code.
- Task CLI: `python tools/tasks.py status | next | show <ID> | validate -w | board`.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `uv`/`just` not found right after installing | open a new terminal (PATH is only read at startup); run `uv tool update-shell` for `just` |
| `docker` errors about WSL | finish `wsl --install`, restart Windows, start Docker Desktop |
| `gcloud` installer asks for administrator | expected: approve the UAC prompt |
