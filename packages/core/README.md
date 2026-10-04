# fantasy-core

Shared NBA-project foundations. Domain-neutral pieces (clock, errors, logging, jobs, snapshot store, HTTP client) moved to the `dikit` kernel (GEN-003). The layering is `core ← ingest`, `core ← features ← models ← decision`.

## Public interface
| Module | Provides |
|---|---|
| `fantasy_core.settings` | `Settings` (pydantic-settings; secrets are `SecretStr`), `load_settings(env_file)`, cached `get_settings()`. Invalid config raises `ConfigError` |
| `fantasy_core.gamedate` | `game_date(ts)` → the US/Eastern date of an instant; `et_day_bounds_utc(d)` → the UTC [start, end), DST-safe (23/24/25 h) |

## Rules
- Domain code never calls `datetime.now()`. It takes a `Clock` or an `AsOf`.
- All stored timestamps are aware UTC. NBA "game date" is US/Eastern.
