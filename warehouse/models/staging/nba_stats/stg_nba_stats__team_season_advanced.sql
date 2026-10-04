-- Team pace and offensive/defensive rating per regular season (LeagueDashTeamStats, Advanced; DATA-038).
with parsed as (
    {{ nba_stats_rows('leaguedashteamstats', '%measure=advanced') }}
)

select
    regexp_extract(snapshot_key, r'season=([^/]+)') as season,
    {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
    {{ nba_stats_col('PACE', 'float64', 'pace') }},
    {{ nba_stats_col('OFF_RATING', 'float64', 'off_rating') }},
    {{ nba_stats_col('DEF_RATING', 'float64', 'def_rating') }},
    observed_at
from parsed
