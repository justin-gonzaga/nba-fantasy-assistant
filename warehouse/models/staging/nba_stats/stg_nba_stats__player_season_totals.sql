-- One row per player per regular season (LeagueDashPlayerStats, PerMode = Totals).
-- A traded player has one combined row; nba_team_id is the team at capture time.
with parsed as (
    {{ nba_stats_rows('leaguedashplayerstats') }}
)

select
    regexp_extract(snapshot_key, r'season=([^/]+)') as season,
    {{ nba_stats_col('PLAYER_ID', 'int64', 'nba_player_id') }},
    {{ nba_stats_col('PLAYER_NAME', 'string', 'player_name') }},
    {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
    {{ nba_stats_col('AGE', 'float64', 'age') }},
    {{ nba_stats_col('GP', 'int64', 'games_played') }},
    {{ nba_stats_col('MIN', 'float64', 'minutes') }},
    {{ nba_stats_col('FGM', 'int64', 'fgm') }},
    {{ nba_stats_col('FGA', 'int64', 'fga') }},
    {{ nba_stats_col('FG3M', 'int64', 'fg3m') }},
    {{ nba_stats_col('FG3A', 'int64', 'fg3a') }},
    {{ nba_stats_col('FTM', 'int64', 'ftm') }},
    {{ nba_stats_col('FTA', 'int64', 'fta') }},
    {{ nba_stats_col('REB', 'int64', 'reb') }},
    {{ nba_stats_col('AST', 'int64', 'ast') }},
    {{ nba_stats_col('STL', 'int64', 'stl') }},
    {{ nba_stats_col('BLK', 'int64', 'blk') }},
    {{ nba_stats_col('TOV', 'int64', 'tov') }},
    {{ nba_stats_col('PTS', 'int64', 'pts') }},
    observed_at
from parsed
