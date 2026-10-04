-- Every NBA draft pick (DraftHistory, all years).
with parsed as (
    {{ nba_stats_rows('drafthistory') }}
)

select
    {{ nba_stats_col('PERSON_ID', 'int64', 'nba_player_id') }},
    {{ nba_stats_col('PLAYER_NAME', 'string', 'player_name') }},
    {{ nba_stats_col('SEASON', 'int64', 'draft_year') }},
    {{ nba_stats_col('ROUND_NUMBER', 'int64', 'round_number') }},
    {{ nba_stats_col('ROUND_PICK', 'int64', 'round_pick') }},
    {{ nba_stats_col('OVERALL_PICK', 'int64', 'overall_pick') }},
    {{ nba_stats_col('DRAFT_TYPE', 'string', 'draft_type') }},
    {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
    {{ nba_stats_col('ORGANIZATION', 'string', 'organization') }},
    {{ nba_stats_col('ORGANIZATION_TYPE', 'string', 'organization_type') }},
    observed_at
from parsed
