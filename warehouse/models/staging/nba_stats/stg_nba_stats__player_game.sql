-- One row per player per regular-season game (LeagueGameLog, PlayerOrTeam = P).
with parsed as (
    {{ nba_stats_rows('leaguegamelog', '%player_or_team=P') }}
)

select
    regexp_extract(snapshot_key, r'season=([^/]+)') as season,
    {{ nba_stats_col('PLAYER_ID', 'int64', 'nba_player_id') }},
    {{ nba_stats_col('PLAYER_NAME', 'string', 'player_name') }},
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
    {{ nba_stats_col('OREB', 'int64', 'oreb') }},
    {{ nba_stats_col('DREB', 'int64', 'dreb') }},
    {{ nba_stats_col('REB', 'int64', 'reb') }},
    {{ nba_stats_col('AST', 'int64', 'ast') }},
    {{ nba_stats_col('STL', 'int64', 'stl') }},
    {{ nba_stats_col('BLK', 'int64', 'blk') }},
    {{ nba_stats_col('TOV', 'int64', 'tov') }},
    {{ nba_stats_col('PF', 'int64', 'pf') }},
    {{ nba_stats_col('PTS', 'int64', 'pts') }},
    {{ nba_stats_col('PLUS_MINUS', 'int64', 'plus_minus') }},
    observed_at
from parsed
