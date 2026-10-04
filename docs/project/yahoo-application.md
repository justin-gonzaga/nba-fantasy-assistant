# Yahoo Fantasy Sports API — Access Application (ready to submit)

_Updated 2026-09-25 to match the actual form at https://sports.yahoo.com/developer/access/. The owner submits it; Claude does not._

Yahoo's guidance: *"Applications must clearly identify the product being built, the Yahoo Fantasy Sports data required, and the intended user base, including where access is limited to personal or single league use."* Incomplete submissions are closed without reply, so the Notes below cover all three explicitly.

## Field 1: Expected Users
**Small (<1,000)**

## Field 2: Notes (copy-paste)
> **Product:** A personal, non-commercial decision-support tool for a single private Yahoo Fantasy Basketball league (NBA, H2H categories) that I play in with friends. It combines my league's settings, rosters and matchups with public NBA statistics, and suggests lineup and roster decisions to me, with explanations. It's also a personal portfolio/learning project.
>
> **Intended users:** Personal / single-league use: me, and possibly a few invited managers from the same league (under 20 people). There's no public product, and no sale or monetisation of any kind.
>
> **Yahoo Fantasy data required (read-only):** For my own league only: league settings (scoring categories, roster positions, limits), team rosters, the matchup schedule/scoreboard, transactions, the free-agent list with ownership %, and draft results. No write access is needed. I won't make automated roster moves.
>
> **Usage and data handling:** Low volume (a few hundred requests per day at most, cached). Other managers' names are pseudonymised on ingestion. Data is stored privately, with a one-step deletion of all Yahoo-derived data. Nothing is redistributed or shown publicly (any public demo of the project uses synthetic or anonymised data). "Data from Yahoo Fantasy Sports" attribution is shown wherever Yahoo data appears. I'll comply with the API Access and Use Agreement (single developer account).
>
> **Context:** My existing app (below) stopped working after the July 2026 change. I'm located in Australia; my league is a standard Yahoo NBA league.

## Field 3: Client ID (optional)
Paste the **Client ID** from your existing app page (App ID s6GZFZED). The Client ID is not a secret. **Do not** paste the Client Secret.

---
### After submitting
- [ ] Tell Claude the submission date → recorded in YAHOO-001
- [ ] If approved, the new credentials come via the app page. At that point, rotate the exposed secret (create a fresh app if Yahoo requires it)
