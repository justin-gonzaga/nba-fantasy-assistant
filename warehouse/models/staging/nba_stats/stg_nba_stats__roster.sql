-- Current roster per team (CommonTeamRoster). A player traded between two team snapshots
-- could appear twice; the latest capture wins.
with parsed as (
    {{ nba_stats_rows('commonteamroster') }}
),

typed as (
    select
        regexp_extract(snapshot_key, r'season=([^/]+)') as season,
        {{ nba_stats_col('TeamID', 'int64', 'nba_team_id') }},
        {{ nba_stats_col('PLAYER_ID', 'int64', 'nba_player_id') }},
        {{ nba_stats_col('PLAYER', 'string', 'player_name') }},
        {{ nba_stats_col('POSITION', 'string', 'nba_position') }},
        {{ nba_stats_col('HEIGHT', 'string', 'height') }},
        {{ nba_stats_col('WEIGHT', 'int64', 'weight_lb') }},
        {{ nba_stats_col('BIRTH_DATE', 'string', 'birth_date_text') }},
        {{ nba_stats_col('AGE', 'float64', 'age') }},
        {{ nba_stats_col('EXP', 'string', 'experience_text') }},
        {{ nba_stats_col('SCHOOL', 'string', 'school') }},
        {{ nba_stats_col('HOW_ACQUIRED', 'string', 'how_acquired') }},
        observed_at
    from parsed
)

select
    season,
    nba_team_id,
    nba_player_id,
    player_name,
    nullif(nba_position, '') as nba_position,
    height,
    weight_lb,
    safe.parse_date('%b %d, %Y', birth_date_text) as birth_date,
    age,
    if(experience_text = 'R', 0, safe_cast(experience_text as int64)) as experience_years,
    school,
    how_acquired,
    observed_at
from typed
qualify row_number() over (partition by season, nba_player_id order by observed_at desc) = 1
