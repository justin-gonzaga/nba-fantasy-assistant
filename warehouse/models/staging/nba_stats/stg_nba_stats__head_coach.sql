-- One head coach per team and season (DATA-038), from CommonTeamRoster's Coaches result set.
-- The endpoint lists the end-of-season staff: a mid-season change shows only the final coach.
with parsed as (
    {{ nba_stats_rows('commonteamroster', result_set=1) }}
),

typed as (
    select
        regexp_extract(snapshot_key, r'season=([^/]+)') as season,
        {{ nba_stats_col('TEAM_ID', 'int64', 'nba_team_id') }},
        {{ nba_stats_col('COACH_ID', 'int64', 'coach_id') }},
        {{ nba_stats_col('COACH_NAME', 'string', 'coach_name') }},
        {{ nba_stats_col('COACH_TYPE', 'string', 'coach_type') }},
        {{ nba_stats_col('SORT_SEQUENCE', 'int64', 'sort_sequence') }},
        observed_at
    from parsed
)

select season, nba_team_id, coach_id, coach_name, observed_at
from typed
where coach_type = 'Head Coach'
qualify row_number() over (
    partition by season, nba_team_id order by observed_at desc, sort_sequence nulls last, coach_id
) = 1
