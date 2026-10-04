# NBA Data Sources — Findings

Living record of what the NBA sources actually do. Each section cites its spike task. See also `2026-09-initial-research.md` §2.

## stats.nba.com via nba_api (DISC-003, 2026-09-25, home IP, Sydney)

**Verdict: works reliably from the home connection. Use 1.0 s between requests.**

### Endpoints verified (AC1)
| Purpose | nba_api endpoint | Call | Latency | Rows |
|---|---|---|---|---|
| Player game logs, league-wide, one season | `LeagueGameLog(season, player_or_team_abbreviation="P")` | 1 request per season | 1.7 s | 26,651 (2025-26) |
| Team game logs, one season | `LeagueGameLog(..., "T")` | 1 per season | 0.3 s | 2,460 |
| Active players (roster reference) | `CommonAllPlayers(season="2026-27", is_only_current_season=1)` | 1 | 0.4 s | 598 |
| Team roster | `CommonTeamRoster(team_id, season)` | 1 per team (30) | 0.4 s | 28 (BOS) |
| Season per-game player stats | `LeagueDashPlayerStats(season, per_mode_detailed="PerGame")` | 1 per season | 0.35 s | 582 |
| Full season schedule | `ScheduleLeagueV2(season="2026-27")` | 1 | 1.7 s | 174 dates, 1,274 games incl. preseason. **Regular season: 20 Oct 2026 → 11 Apr 2027** |
| Advanced box score, one game | `BoxScoreAdvancedV3(game_id)` | 1 per game | 0.6 s | — |

The schedule games include `gameDateTimeUTC`, `gameDateEst`, `homeTeam`/`awayTeam`, and `gameStatus`, which are enough for game-date and back-to-back logic.

### Pacing test (AC2): 100 sequential box-score requests per setting
| Pause between requests | Success | Latency p50 | Latency p95 |
|---|---|---|---|
| 0.6 s | 100 % (0 failures) | 0.68 s | 0.93 s |
| 1.0 s | 100 % (0 failures) | 0.29 s | 0.44 s |

**Interpretation:** no hard blocking at either pace. At 0.6 s, though, responses were ~2× slower, a likely sign of soft throttling.
**Recommendation: 1.0 s minimum spacing**, with exponential backoff on timeouts, and resumable checkpoints for backfills.

### Backfill estimate (AC3): 3 seasons (2023-24 … 2025-26)
| Data | Requests | Time at 1.0 s + ~0.3 s |
|---|---|---|
| Player + team game logs | 2 per season × 3 = 6 | < 1 min |
| Season per-game stats | 3 | < 1 min |
| Rosters (current) | 30 | ~1 min |
| Advanced box scores (optional) | ~1,230 games × 3 = ~3,690 | **~80 min** |

So the core history needed for the draft (game logs + season stats) takes **minutes**. Advanced box scores are an optional ~1.5 h resumable job.

### Fixtures (AC4)
`packages/ingest/tests/fixtures/nba_stats/`: one truncated, valid-JSON sample per endpoint (the first 25 rows; the schedule's first 2 regular-season dates). This is public NBA data, with no personal information.

### Caveats
- These are unofficial endpoints, so their shape can change without notice. The contract tests (DATA-009) will catch that.
- Measured from a residential IP only. Cloud IPs are reported blocked, which is why this runs as a local job (ADR-0019, ADR-0020).
- There was no rate-limit response at all tonight, so the true ceiling is unknown. 1.0 s is conservative on purpose.

## cdn.nba.com static JSON (DISC-004, 2026-09-25, home IP)

**Verdict: complete schedule + box scores for fantasy. Requests must send browser-style headers, otherwise every request gets HTTP 403.**

| Check | Result |
|---|---|
| Headers | Plain requests → **403** on every URL. With `User-Agent` (browser), `Referer: https://www.nba.com/`, `Origin: https://www.nba.com`, `Accept` → **200**. The ingest client must always send these |
| Schedule `staticData/scheduleLeagueV2_1.json` | 200, 4.7 MB, 1.5 s; season 2026-27; 1,274 games (1,206 regular + 67 preseason + 1 other); first regular tip 2026-10-20T19:00Z; IDs `00226xxxxx` (regular = `002`, preseason = `001`) |
| Box scores `liveData/boxscore/boxscore_{gameId}.json`, 20 random 2025-26 regular-season games | **20/20 OK**, p50 0.54 s at 0.5 s spacing |
| Preseason 2026-27 box scores | 403 for all 5 sampled: they haven't been played yet (first 3 Oct). The CDN returns 403 (not 404) for missing files, so a **403 must not be treated as a block** without checking the game status in the schedule first |
| Scoreboard / odds (today) | 200 / 200 |
| Cloud reachability | **Not tested** (no cloud host yet). Verify from Cloud Run during INFRA-004 (A-03 remains partly open) |

**Player box-score fields** (all fantasy categories present): `personId, name, position, starter, played, status, oncourt` + statistics: `points, reboundsTotal/Offensive/Defensive, assists, steals, blocks, turnovers, threePointersMade/Attempted, fieldGoalsMade/Attempted, freeThrowsMade/Attempted, minutes (ISO-8601 duration, e.g. PT32M10.00S), plusMinusPoints, foulsPersonal, pointsInThePaint, …`. Double-doubles/triple-doubles are derived.

**Fixtures**: `packages/ingest/tests/fixtures/nba_cdn/`: a schedule sample (first regular-season date) and a box-score sample (3 players per side).

**A-03 update**: box scores for the previous season: ✅ confirmed. Current-season preseason: pending until games are played. From the cloud: open.

## Official injury report PDFs (DISC-005, 2026-09-25)

**Verdict: build our own pure-Python parser (pdfplumber, column-position based). Don't depend on `nbainjuries`.**

### URL pattern and cadence (AC1)
- `https://ak-static.cms.nba.com/referee/injury/Injury-Report_{YYYY-MM-DD}_{time}.pdf` (from the `nbainjuries` source, confirmed by downloads).
- **Two filename formats:**
  - legacy hourly `…_05PM.pdf`: seen from 2022 through **Nov 2025**. The file labelled `05PM` is actually the **5:30 PM** report (per the header).
  - new `…_05_00PM.pdf` / `…_05_15PM.pdf` (15-minute cadence): in use by **Jan 2026**, 403 for the same slots in Nov 2025.
  - The switch happened between Nov 2025 and Jan 2026, so the fetcher must try both formats.
- A missing file returns 403 (same as the CDN), so try the slots and treat 403 as "not published".
- **Point-in-time:** the report timestamp printed in the PDF header is the authoritative `valid_at`; our fetch time is `observed_at`.
- Downloaded 12 reports across 2022–2026 (6–11 pages, 76–91 KB each).

### `nbainjuries` evaluation (AC2)
- v1.1.1, MIT licence, reasonably maintained.
- **It needs a Java runtime** (tabula-py via jpype). Import fails without a JVM. That's a heavy, awkward dependency for a Cloud Run container, and a fragile one on the dev machine.
- It's useful as a **reference** (URL formats, season calendars), not as a runtime dependency.

### Own parser prototype (AC3)
- Plain text extraction is **wrong for this layout**:
  - spaces between words are dropped ("PhoenixSuns")
  - **reasons wrap onto lines above and below** the player line
  - date, time, matchup and team only appear on the first row of each group
- Positional parsing works: header x-positions define the columns (found with default word spacing); content is read with tight spacing; wrapped reason fragments attach to the nearest player row; game context carries forward.

| Reports | Result |
|---|---|
| 9 reports, May 2023 → Mar 2026 (both filename formats) | parsed: 18–165 rows each; **0 rows missing a reason or context**; a manual spot-check of the first 12 rows of 2026-01-20 matches the PDF, including wrapped reasons like "Injury/Illness - Right Knee; Injury Management" |
| 3 reports, Jan 2022 → Mar 2023 | **0 rows**: an older layout variant (the header/columns differ). Not solved within the spike's 3-attempt cap. A **DATA-007 acceptance criterion** now requires it (needed for the 2021-22+ history in DATA-010) |

Fixtures: `packages/ingest/tests/fixtures/injury_reports/`: a new-format PDF + its expected first 12 rows, a 2025 legacy PDF, and a 2022 old-layout PDF (the failing case, kept as a regression target).

### Recommendation (AC4)
**Own parser**: pdfplumber, pure Python, versioned `extractor_version`, golden tests per layout era. `nbainjuries` is used only as a reference for URL/calendar logic.

## Team and head-coach context (DATA-038, 2026-10-03, home IP)
Checked live on 2026-10-03 for ANL-010's team/coach study.

| Need | Endpoint | Fields | Notes |
|---|---|---|---|
| Head coach per team-season | `commonteamroster` (TeamID, Season) | `Coaches` result set (resultSets[1]): `COACH_ID`, `COACH_NAME`, `COACH_TYPE` = "Head Coach" | Past seasons return that season's staff, but the **end-of-season** coach: MIL 2023-24 lists Doc Rivers, who replaced Adrian Griffin mid-season. Mid-season changes are not visible; off-season changes are. A coach fired **after** the season leaves no head coach in the list (10 of 341 team-seasons 2015-16 → 2025-26, e.g. LAL and SAC 2015-16). |
| Pace and ratings | `leaguedashteamstats`, MeasureType=Advanced, PerMode=PerGame | `PACE`, `OFF_RATING`, `DEF_RATING` per `TEAM_ID` | All 30 teams per regular season. Empty filters go as empty strings, as for `leaguedashplayerstats`. |
| Minutes / shot concentration | none (derived) | top-3 share of team minutes and FGA from `leaguegamelog` (players) | computed in `int_team_season_context` |

- **Fetch**: `fantasy team-context-backfill` (resumable; 30 rosters + 1 team table per season, 1 s pacing), home IP
  only (D-63). Raw lands under `raw/nba_stats/commonteamroster/season=<s>/team_id=<t>/` and
  `raw/nba_stats/leaguedashteamstats/season=<s>/measure=advanced/`.
- **Point in time**: the warehouse keeps the latest capture per season; a projection that must not see later news
  reads the roster through `SnapshotStore.as_of(…, t)` (`team_context.head_coach_as_of`).
- **Terms**: stats.nba.com has no published API terms for personal use; the same pacing and home-IP rule as the
  other stats.nba.com fetches applies (DISC-003).
