# Owner Setup Checklist

These are the one-time steps only a human can do: they need a browser, a password, or a payment method. After them,
Claude can work without you. Check progress at any time with:

```powershell
python tools/doctor.py     # shows ✓/✗ per item; never prints secret values
```

> **If a command isn't found**, the terminal was opened before the tool was installed. Paste this first, or restart VS Code:
> ```powershell
> $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
> ```

## Step 0: Create your local secrets file (1 min)
```powershell
Copy-Item env.example .env
code .env        # fill in values as you go through the steps below; save
```

## Step 1: GitHub login (2 min) → unblocks the repo and CI
```powershell
gh auth login
```
Choose **GitHub.com → HTTPS → Y → Login with a web browser**, then paste the one-time code into the browser.

## Step 2: Google Cloud (10 min) → unblocks the infrastructure
1. Go to **console.cloud.google.com**, sign in with your Google account, accept the terms, and **create a billing account** (a card is required; the budget alert will be set at US$10/mo).
2. Copy the **Billing account ID** (Billing → Account management, format `XXXXXX-XXXXXX-XXXXXX`) into `infra/terraform/bootstrap/terraform.tfvars` as `billing_account = "…"` (gitignored; copy it from `terraform.tfvars.example`). It isn't a secret, but it must stay out of the public repo.
3. In PowerShell, run these two commands. Each opens a browser; sign in and approve.
   ```powershell
   gcloud auth login
   gcloud auth application-default login
   ```
4. **Access model (I5):** after the one-time bootstrap (INFRA-001), Claude's sessions will *impersonate a dev-only service account*, so your owner-level login is only used to create the projects.

## Step 3: Yahoo developer app (5 min) → unblocks the draft helper and data collection
1. Go to **developer.yahoo.com/apps/create** (sign in with the Yahoo account that's in the league).
2. Fill in:
   - **Application Name**: `nba-fantasy-assistant`
   - **Application Type**: *Confidential Client*
   - **Redirect URI(s)**: `https://localhost:8080`
   - **API Permissions**: tick **Fantasy Sports → Read**
3. Click **Create App**. Copy the **Client ID** and **Client Secret** into `.env` as `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET`.
4. Later (DISC-001), Claude will ask you to run `just yahoo-login` once. It opens Yahoo's consent page; you click **Agree** and paste the code back into the terminal.

## Step 4: Telegram bot (3 min) → unblocks phone alerts
1. In Telegram, open **@BotFather** → send `/newbot` → choose a name (e.g. *Courtside Assistant*) and a username ending in `bot`.
2. Copy the **token** into `.env` as `TELEGRAM_BOT_TOKEN`.
3. Open your new bot and send it `/start`. That lets it message you.

## Step 5: Docker Desktop engine (2 min)
- Quit Docker Desktop (right-click the whale icon → Quit) and reopen it. If it still says "unable to start", restart Windows.
- It's ready when `docker run --rm hello-world` prints "Hello from Docker!".

## Later, not needed now
| Item | When |
|---|---|
| Anthropic API key (console.anthropic.com; separate billing from Claude Pro) | Before the natural-language question feature (Phase 7) |
| healthchecks.io account (free) | FND-013 (alerting) |
| Apple Developer account (US$99/yr) | Only if the iOS app goes ahead (G-18) |

## Safety notes
- `.env` is gitignored, and Claude is blocked from reading it. Secrets go to Google Secret Manager during INFRA-003.
- Never paste secrets into a chat with Claude; `python tools/doctor.py` only reports whether each one is set.
