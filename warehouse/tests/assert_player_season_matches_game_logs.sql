-- DATA-029 AC3: int_player_season (built from game logs) agrees with the official season totals.
-- Error: a player-season missing on either side, a games-played mismatch, or any stat off by > 3.
-- Stat corrections that reach only one feed show up as differences of 1–3; those are
-- reported by assert_player_season_exact_match (warn) instead.
{%- set stats = ['pts', 'fgm', 'fga', 'fg3m', 'ftm', 'fta', 'reb', 'ast', 'stl', 'blk', 'tov'] %}
select
    season, nba_player_id, i.player_name,
    i.games_played, t.games_played as official_games
from {{ ref('int_player_season') }} as i
full outer join {{ ref('stg_nba_stats__player_season_totals') }} as t using (season, nba_player_id)
where i.nba_player_id is null
    or t.nba_player_id is null
    or i.games_played != t.games_played
    {%- for s in stats %}
    or abs(i.{{ s }} - t.{{ s }}) > 3
    {%- endfor %}
