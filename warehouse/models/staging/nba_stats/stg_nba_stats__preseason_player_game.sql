-- One row per player per pre-season game (LeagueGameLog, SeasonType = Pre Season; DATA-030).
with parsed as (
    {{ nba_stats_rows('leaguegamelog', '%player_or_team=P/season_type=pre_season') }}
)

select
    *,
    -- a few source rows have negative minutes (e.g. visiting international teams, 2017): unusable
    if(minutes_raw < 0, null, minutes_raw) as minutes
from (
select
    regexp_extract(snapshot_key, r'season=([^/]+)') as season,
    {{ nba_stats_col('PLAYER_ID', 'int64', 'nba_player_id') }},
    {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
    {{ nba_stats_col('GAME_ID', 'string', 'nba_game_id') }},
    {{ nba_stats_col('GAME_DATE', 'date', 'game_date') }},
    {{ nba_stats_col('MIN', 'float64', 'minutes_raw') }},
    {{ nba_stats_col('PTS', 'int64', 'pts') }},
    observed_at
from parsed
)
