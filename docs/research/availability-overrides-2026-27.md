# Availability overrides 2026-27 (research note, 2026-09-26)

Method: a researcher agent searched current news (September 2026) for players expected to miss significant time. Each entry needs a public source, its date and a quote. The main session re-checked that each source URL resolves; the owner reviewed and approved the list on 2026-09-26 (DATA-031 AC3).

| Player | Team | Status | Games cap | Source (date) | Re-checked |
|---|---|---|---|---|---|
| Henri Veesaar | ATL | out (season) | 0 | ESPN (2026-09-21) | yes (HTTP 200) |
| Jalen Duren | DET | holdout risk | tag only | Hoops Rumors (2026-09-21) | yes (HTTP 200) |
| Brandon Ingram | LAC | questionable start | tag only | CBS Sports (2026-09-23) | no (site blocked automated access) |

**Reported cleared** (no override): Tyrese Haliburton, Kyrie Irving, Damian Lillard, Ja Morant, Joel Embiid, Victor Wembanyama, Zion Williamson.

**Re-check in draft week, after media day (~29 Sep–3 Oct):**
- Paul George, Moses Moody, Klay Thompson and Michael Porter Jr. (search results mixed seasons, so these are unverified)
- the Duren contract
- Ingram's timeline

The data file is `warehouse/seeds/availability_overrides.csv`; the rules are in `apps/pipeline/src/fantasy_pipeline/overrides.py`.
