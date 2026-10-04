-- Warn-level companion of assert_player_season_matches_game_logs: lists player-seasons where
-- any stat differs at all between the game logs and the official totals (stat corrections).
-- 2026-09-25 baseline: 63 of 5,968 player-seasons, max difference 3 (rebounds).
{{ config(severity='warn') }}
{%- set stats = ['pts', 'fgm', 'fga', 'fg3m', 'ftm', 'fta', 'reb', 'ast', 'stl', 'blk', 'tov'] %}
select season, nba_player_id, i.player_name
from {{ ref('int_player_season') }} as i
join {{ ref('stg_nba_stats__player_season_totals') }} as t using (season, nba_player_id)
where false
    {%- for s in stats %}
    or i.{{ s }} != t.{{ s }}
    {%- endfor %}
