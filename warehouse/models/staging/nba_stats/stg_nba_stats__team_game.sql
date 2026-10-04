-- One row per team per regular-season game (LeagueGameLog, PlayerOrTeam = T).
with parsed as (
    {{ nba_stats_rows('leaguegamelog', '%player_or_team=T') }}
)

select
    regexp_extract(snapshot_key, r'season=([^/]+)') as season,
    {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
    {{ nba_stats_col('TEAM_ABBREVIATION', 'string', 'team_abbreviation') }},
    {{ nba_stats_col('GAME_ID', 'string', 'nba_game_id') }},
    {{ nba_stats_col('GAME_DATE', 'date', 'game_date') }},
    {{ nba_stats_col('MATCHUP', 'string', 'matchup') }},
    {{ nba_stats_col('WL', 'string', 'win_loss') }},
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
