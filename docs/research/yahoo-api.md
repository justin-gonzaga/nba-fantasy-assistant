# Yahoo Fantasy API — Findings

## DISC-001 (2026-09-25): the API is closed to existing apps
**Verdict: the self-serve Yahoo Fantasy API no longer works. Every endpoint returns HTTP 403 "This application is not authorized to perform this action", for all existing apps, since 22 Jul 2026.**

| Check (our app, App ID s6GZFZED, "Fantasy Sports - Read" shown as granted) | Result |
|---|---|
| OAuth2 consent (authorization-code) | ✅ works; access token lifetime 3600 s |
| Refresh-token grant | ✅ works |
| Token response scope | absent (keys: access_token, refresh_token, expires_in, token_type) |
| `game/nba` (public metadata) | 403 not authorized |
| `games;game_codes=nba;seasons=2026` | 403 |
| `users;use_login=1`, `…/games`, `…/games;game_codes=nba/leagues` | 403 |
| OpenID `userinfo` | 403 (no openid scope requested) |

**Cause (external, confirmed):**
- yfpy issue #84 reports the same 403 on all endpoints since 2026-07-22 (US/Eastern). The create-app form no longer offers Fantasy Sports. Fresh apps, PKCE and re-consent all fail. There's no Yahoo statement, no workaround, and it's still open. https://github.com/uberfastman/yfpy/issues/84 (accessed 2026-09-25)
- Yahoo's docs now lead to an **approval-based developer programme**: submission (organisation, product, use case) → review → access. Eligibility for personal projects, review time and fees are unstated. Attribution to Yahoo is required, and only a single developer account is allowed. https://sports.yahoo.com/developer/ (accessed 2026-09-25)
- This follows an earlier silent removal of write access (Oct 2025), per the same issue.

## Consequences and decisions (owner, 2026-09-25; D-43, D-44, ADR-0025)
- **Apply** to the new programme (honestly: personal, non-commercial, portfolio/research; Yahoo attribution) → task YAHOO-001.
- **Fallback, built in parallel: assisted import.** The owner sends a screenshot or copy-paste of their own Yahoo page (league settings once; a roster page after moves; the matchup schedule once) to the Telegram bot or dashboard. A parser/LLM extracts it; the owner confirms; it's stored as a raw snapshot with `observed_at`.
- **What we no longer get automatically:** league-wide ownership %, the Yahoo FA list/ranks, and waiver/transaction feeds. We derive what we can instead:
  - FA pool = the NBA player universe minus rostered players
  - matchup scores = NBA box scores + league rules
  - ownership % = unavailable
- **Draft:** live helper input by quick pick entry (autocomplete, ~2 s per pick).
- Point-in-time Yahoo history becomes owner-import-driven (lower cadence). The evaluation standard notes this limitation.
- The client secret was exposed in a chat screenshot. Rotate it when new access arrives; otherwise delete the old app.

## DISC-007 (2026-09-27): Yahoo terms and data retention

**Conclusion first.** There are still no fantasy-specific API terms: the page returns 404, confirmed on 2026-09-24 and again on 2026-09-27. The general API Terms of Use and the consumer Terms of Service are live and quoted below. Nothing here changes G-04 (APPROVED, A2). The open question is also unchanged: whether the 24-hour deletion clause binds only API users (which we are not, under assisted import) or applies more broadly. No Yahoo statement resolves it. This is research, not legal advice.

### Sources (accessed 2026-09-27)

| Page | URL | Last updated shown | Status |
|---|---|---|---|
| Yahoo Developer API Terms of Use | https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html | none; footer "REV 3-2022" | live |
| Yahoo Fantasy Sports APIs: Terms of Use | https://legal.yahoo.com/us/en/yahoo/terms/product-atos/fantasysportsapi/index.html | n/a | **404** (twice). The Wayback Machine could not be fetched from this environment; check it manually in a browser |
| Yahoo Terms of Service (consumer) | https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html | no date in the body; a `previousversion-2025-06-09` sibling exists | live |
| Yahoo Sports Fantasy Basketball Additional Terms | https://legal.yahoo.com/us/en/yahoo/terms/product-atos/fantasy-basketball/general/index.html | none | live |
| Yahoo Daily Fantasy data retention | https://policies.yahoo.com/us/en/yahoo/terms/dataretention/fantasysports/index.htm | none | live; Daily Fantasy only, **not** season-long leagues |

### Clauses (verbatim, as fetched by the researcher subagent)

1. **24-hour deletion** (API ToU): "You may not retain or use, and must immediately remove from any Application and any data repository in your possession or under your control any Yahoo user data obtained through the Yahoo APIs that is not explicitly identified as being storable indefinitely in the API Documents within 24 hours after the time at which you obtained the data". The exceptions would be listed in the fantasy API documents, which are the 404 page.
2. **No third-party access** (API ToU): "You may not disclose any Yahoo user data or store any Yahoo user data in any data repository that enables any third party (other than the Yahoo user) access unless such disclosure or third party access is expressly permitted by the Yahoo user"
3. **No income from the APIs** (API ToU): "Sell, lease, share, transfer, or sublicense the Yahoo APIs or access or access codes thereto or derive income from the use or provision of the Yahoo APIs, whether for direct commercial or monetary gain or otherwise, unless the API Documents specifically permit otherwise"
4. **User consent for OAuth access** (API ToU): "You are solely responsible for securing clear, express consent from the user, granting you permission to access such user's Yahoo account using OAuth-enabled APIs." No clause addresses consent for *other* managers' data that appears in a league.
5. **No automated collection** (consumer ToS §2.4(ix)): "access or collect data, or attempt to access or collect data, from our Services using any automated means, devices, programs, algorithms or methodologies, including but not limited to robots, spiders, scrapers, data mining tools, or data gathering or extraction tools, for any purpose without our express, prior permission."
6. **No competing database** (consumer ToS §2.4(x)): "use any material or content from, including without limitation any data, (a) to create any database, archive, mobile application, data feed, widget or any other aggregated data source that competes with or constitutes a material substitute for the Services"
7. **No commercial reuse by default** (consumer ToS §2.5): "Unless otherwise expressly stated, you may not access or reuse the Services, or any portion thereof, for any commercial purpose."
8. **Fantasy Basketball terms incorporate the ToS**: "which supplement the Yahoo Terms of Service ("TOS"), located at [https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html], and are hereby incorporated by reference"
9. **Entertainment only**: "Fantasy Basketball is for entertainment purposes only and may not be used in connection with any form of gambling or wagering or for any other commercial endeavors."

Excluded: a search-engine summary attributed further fantasy-API clauses (a single-account rule and a territorial licence) to the 404 URL. The page itself couldn't be read, so these are **UNVERIFIED** and not used.

### What it means for each mode (interpretation, with uncertainty)

- **(a) Owner-pasted assisted import (today, ADR-0025).**
  - No API is called, so clauses 1-4 bind API users, not us.
  - Clause 5 matters only if a script or headless browser touched yahoo.com. A human copying and pasting is plausibly not "automated means", but that is our reading, not Yahoo's.
  - Clause 6 plausibly doesn't reach a private, single-league tool.
  - Clauses 7 and 9 (non-commercial) are met by design.
  - Pseudonymising other managers is our own design choice. No clause requires it.
- **(b) A future approved API app.**
  - Clauses 1-4 would apply directly.
  - Keeping point-in-time history (ADR-0005) would need either named "storable indefinitely" exceptions in the fantasy API documents or written permission from Yahoo.

### Open items
1. Check the Wayback Machine for the fantasy API terms URL manually in a browser.
2. Re-read the API documents if YAHOO-001 gets a reply.

## League settings, via assisted import (owner paste, 2026-09-25)
Raw copy: `data/samples/yahoo/league_settings.txt` (gitignored). Scrubbed fixture: `packages/ingest/tests/fixtures/yahoo_import/league_settings_h2h9cat_auction.txt`.

| Setting | Value | Design impact |
|---|---|---|
| Scoring | **H2H Categories, 9-cat**: FG%, FT%, 3PTM, PTS, REB, AST, ST, BLK, TO | A-01 **validated**. The first-class objective is `H2HCategories` |
| Teams | **16** | Deep league → low replacement level; the waiver pool is thinner |
| Draft | **Live salary-cap (auction)**, $200 budget, 30 s nomination / 20 s bid | The draft helper needs **auction $ values**, budget/max-bid tracking and nomination advice |
| Draft time | **Sun 18 Oct 2026 02:00 EDT = 17:00 AEDT (Sydney)** | M0.5 deadline: ready + dry run by **Thu 15 Oct** |
| Lineups | Daily, today (locks at each game) | Daily lineup optimiser; per-game lock times |
| Roster | G×3, F×3, C, Util×3, BN×4, IL×3 (10 starters, 17 total) | MILP slot eligibility (G, F, C, Util) |
| Acquisitions | max **4 per week**, no season max; waivers 2 days, continual rolling | Streaming budget = 4/week (a constraint in valuation) |
| Playoffs | 6 teams, weeks 18–20 (ends Sun 21 Mar 2027); higher seed wins ties | Trade/ROS valuation weights the playoff weeks |
| Trade deadline | 4 Mar 2027 | — |
