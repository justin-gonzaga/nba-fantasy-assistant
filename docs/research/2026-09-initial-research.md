# Initial Research — Data Sources, Platform, Claude Code (2026-09-24)

Status: **findings + open assumptions**. Every item marked `UNVERIFIED` must be validated by a
Phase 0 spike task before code depends on it. Cite this file from ADRs rather than re-researching.

---

## 1. Yahoo Fantasy Sports API

| Finding | Confidence | Source |
|---|---|---|
| Official REST API exists; OAuth 2.0 authorization-code flow; app registered on Yahoo Developer Network with "Fantasy Sports: Read" (or Read/Write) scope. | High | [Yahoo developer docs](https://sports.yahoo.com/developer/docs/) |
| Access tokens are short-lived (commonly reported ~1 h; one source says minutes); refresh token grant (`grant_type=refresh_token`) used for long-running access. | Medium — **UNVERIFIED lifetime** | [Medium write-up](https://medium.com/@dcheng47/yahoosportsapi-1265b0e25954), yfpy docs |
| Public docs are football-centric; NBA stat_ids and NBA-specific resource shapes are **not documented** and must be discovered empirically (`/game/nba/stat_categories`, league `settings`). | High | Yahoo docs |
| Rate limits are undocumented and "at Yahoo's sole discretion". | High | [Yahoo API ToU](https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html) |
| **Yahoo API ToU requires deleting Yahoo *user data* within 24 h unless docs say it is storable indefinitely.** Unclear whether league/roster/stat data counts as "user data". Fantasy-specific ToU URL returned 404 on 2026-09-24. | High (clause exists) / **interpretation UNCERTAIN** | Yahoo API ToU |
| Non-commercial use only; no monetisation. Our use (personal, non-commercial) is consistent. | High | Yahoo API ToU |
| Mature Python wrappers: `yfpy` (maintained, OAuth2 incl. programmatic token JSON), `yahoo_fantasy_api`, `yahoofantasy`. | High | [yfpy](https://github.com/uberfastman/yfpy), [PyPI](https://pypi.org/project/yahoo-fantasy-api/) |
| Redirect URI requirements (`oob` vs https) — **UNVERIFIED**; yfpy historically uses an out-of-band copy/paste code. | Low | yfpy README |

**Implications**
- Read-only scope is sufficient for decision support; write scope (auto roster moves) is a deliberate later gate.
- We store raw payloads for point-in-time replay → the 24 h clause is a **human approval gate (G-04)**.
- NBA-specific schema discovery is a Phase 0 spike (DISC-001/002).

## 2. NBA data

| Source | What | Access constraints | Confidence |
|---|---|---|---|
| `cdn.nba.com` static JSON (`scheduleLeagueV2_1.json`, `liveData/boxscore/boxscore_{gameId}.json`, `todaysScoreboard_00.json`) | Full-season schedule, live + completed box scores | Unauthenticated, **reported to work from cloud IPs**; unofficial/undocumented, may change without notice | Medium ([nba_api issue](https://github.com/swar/nba_api/issues/665), [nba_api docs](https://github.com/swar/nba_api/blob/master/docs/nba_api/live/endpoints/boxscore.md)) |
| `stats.nba.com` via `nba_api` | Historical game logs, advanced stats, player/team info, lineups | **Blocks datacenter IPs (AWS/GCP/Azure, incl. GitHub Actions runners) via Akamai**; conservative ~600 ms between requests; unofficial | High ([Medium](https://medium.com/@inman.justin/working-around-nba-coms-ip-ban-for-cloud-hosted-nba-api-apps-90326ab2632c), [nba_api #650](https://github.com/swar/nba_api/issues/650)) |
| Official NBA injury report (PDF, official.nba.com) | Player designations (Out/Doubtful/Questionable/Probable), reasons; published multiple times daily | Public PDFs; parsing required. `nbainjuries` package parses and provides history **since 2021-22** | High ([official.nba.com](https://official.nba.com/nba-injury-report-2025-26-season/), [nbainjuries](https://github.com/mxufc29/nbainjuries)) |
| BALLDONTLIE API | Players, games, stats, injuries, box scores | Free: 5 req/min, core endpoints only. $9.99/mo: stats + injuries, 60 req/min. $39.99/mo: box scores, lineups | Medium ([docs](https://docs.balldontlie.io/)) |
| Basketball-Reference | Historical stats | **≤20 req/min or 24 h block**; data licensed from third parties; not a primary source | High ([bot policy](https://www.sports-reference.com/bot-traffic.html)) |

**Implications**
- Primary: `cdn.nba.com` (schedule, box scores) + `stats.nba.com` for historical backfill **run from a residential IP** (the local machine) + official injury PDFs.
- Paid fallback (BALLDONTLIE $9.99/mo) exists if unofficial endpoints break — keep behind a source interface (G-05).
- Historical *as-of* injury data exists from 2021-22 → enables availability-model training and honest backtests.

### 2a. Owner direction (2026-09-24)
- **No live in-game data is needed.** Final box scores are fetched once after games.
- **History**: download the stats.nba.com data locally (home IP), then upload it to cloud storage. The ongoing daily data comes from cdn.nba.com, reportedly reachable from the cloud (A-03), so after the initial backfill the laptop isn't needed daily. This strengthens the hybrid/cloud options for D-01.
- **Injury reports are needed live.** The official report is published every **15 minutes** on game days ([official.nba.com](https://official.nba.com/nba-injury-report-2025-26-season/)). Reachability from the cloud is UNVERIFIED (DISC-005).
- **Starting lineups will be predicted**, not sourced.
- **News**: the owner proposes LLM-based extraction, scheduled before games, for relevant players only. This is decision D-32, with spike DISC-008.

### 2b. Paid NBA APIs (checked 2026-09-24)
| Provider | Personal price | What you get | Caveats |
|---|---|---|---|
| BALLDONTLIE ([docs](https://docs.balldontlie.io/)) | Free / $9.99 / $39.99 per mo | Free: teams, players, games. $9.99: player game stats, injuries. $39.99: box scores, **lineups**, advanced stats, season averages, odds, play-by-play. History since 1946 (advanced since 1996). 48 h trial of the top tier | Commercial terms not stated; lineup timing (pre-game vs post) UNVERIFIED |
| MySportsFeeds ([pricing](https://www.mysportsfeeds.com/feed-pricing/)) | From **$5/mo** personal (CORE, **non-live/delayed**); commercial from $29/mo | Claims schedules, box scores, lineups, injuries, projections, odds, DFS. Add-on modules are priced separately | Which add-ons the personal plan includes, and how long the delay is, are UNVERIFIED → spike DISC-009 |
| API-Sports ([NBA](https://api-sports.io/sports/nba)) | Free 100 req/day; ~$15–35/mo | Games, stats, standings | Injury/lineup coverage unclear; less fantasy-focused |
| SportsDataIO ([NBA](https://sportsdata.io/nba-api)) | Sales-led; industry estimates $500–1,000+/mo | Everything, incl. **confirmed lineups, news, depth charts, Yahoo-format fantasy points** | Enterprise pricing; a free trial (1,000 calls/mo) is useful for comparison only |
| Sportradar | Enterprise | The official NBA data partner | Out of budget |

## 3. Data platform / hosting (brief)

- dlt + dbt + DuckDB (+ MotherDuck) is the widely used "small data stack"; DuckDB recommended until data outgrows one machine ([dlthub](https://dlthub.com/blog/dlt-motherduck-demo), [Bruin](https://getbruin.com/blog/cheapest-modern-data-stack-2026/)). Our data volume: < 5 GB total, including several historical seasons.
- Hosting: Hetzner VPS ~US$4–5/mo (EU/US/SG regions); Fly.io ~US$2–25/mo metered, no free tier; Cloud Run scale-to-zero but stats.nba.com unreachable from it ([getdeploying](https://getdeploying.com/flyio-vs-hetzner)).

## 4. Calendar

- 2026-27 regular season opens **Tuesday 20 Oct 2026** ([FOX Sports](https://www.foxsports.com/stories/nba/when-does-2026-27-nba-season-start-opening-night-schedule)).
- Consequence: point-in-time snapshots (Yahoo waivers/ownership/rosters, injury designations) **cannot be recreated later**. A minimal snapshot collector should run before tip-off, ahead of any modelling.

## 5. Claude Code capabilities (current docs, 2026-09)

- **Skills**: `.claude/skills/<name>/SKILL.md`; frontmatter includes `description`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context: fork`, `agent`, `model`, `effort`, `paths` (auto-activate by glob), `arguments`; `` !`cmd` `` injects command output. Loaded on demand (progressive disclosure). ([docs](https://code.claude.com/docs/en/skills))
- **Subagents**: `.claude/agents/*.md`; frontmatter `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `hooks`, `memory`, `isolation: worktree`, `effort`. Own context window. ([docs](https://code.claude.com/docs/en/sub-agents))
- **Hooks**: deterministic scripts on `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, `SubagentStop` etc. Rule of thumb: enforce with hooks/permissions, teach with skills, isolate with subagents, keep CLAUDE.md short.
- **Remote Control**: `claude --remote-control` / `/remote-control` / `claude remote-control` (server mode). Session runs on the **local machine**; phone/web steer it. Survives sleep/network drops by reconnecting; machine must be on for work to progress. ([docs](https://code.claude.com/docs/en/remote-control))

## 6. Local environment (observed 2026-09-24)

Windows 11, Git 2.50, Python 3.13.14, Node 22.17. **Not installed:** `uv`, Docker, `gh`, `just`. Installing them is FND-001 (needs G-12).

## 7. Open assumptions (to validate)

| ID | Assumption | Validated by |
|---|---|---|
| A-01 | **Validated 2026-09-25**: H2H Categories 9-cat, daily lineups, 16 teams, auction draft ($200) | owner paste ✅ |
| A-02 | **Confirmed**: Australia/Sydney, awake window 07:00–23:00. Storage is UTC; the NBA "game date" is US/Eastern. | G-13 ✅ |
| A-03 | `cdn.nba.com` box score JSON is retrievable for all games of the current and previous season. **Partly validated (DISC-004)**: 2025-26 20/20 ✅ with browser headers; 2026-27 pending games; cloud reachability open (INFRA-004) | DISC-004 |
| A-04 | ~~Yahoo historical seasons for the same league are retrievable~~ **N/A: the owner confirmed there are no earlier seasons (2026-09-24)** | — |
| A-05 | NBA↔Yahoo player ID crosswalk can be ≥ 99 % automated (name + team + position), remainder via overrides file. | DATA-020 |
| A-06 | The dev machine is on for several hours most days (Remote Control + local scheduled ingestion). | G-06 |
