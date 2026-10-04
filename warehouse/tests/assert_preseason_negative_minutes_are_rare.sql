-- Warn-level DQ check (DATA-030): source rows with negative pre-season minutes are nulled in staging.
-- 2026-09-26 baseline: 5 rows (2017-18 x4, 2023-24 x1). The warning fires whenever any appear.
{{ config(severity='warn') }}
select season, nba_player_id, nba_game_id, minutes_raw
from {{ ref('stg_nba_stats__preseason_player_game') }}
where minutes_raw < 0
