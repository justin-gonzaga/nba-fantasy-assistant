-- Starters in pre-season games from the v3 box score (DATA-030): a non-empty `position` = started.
-- JSON paths must be constants in BigQuery, so home and away are read separately.
with latest as (
    select *
    from {{ ref('stg_nba_stats__snapshots') }}
    where endpoint = 'boxscoretraditionalv3'
    qualify row_number() over (partition by snapshot_key order by observed_at desc) = 1
),

sides as (
    select
        json_value(payload, '$.boxScoreTraditional.gameId') as nba_game_id,
        json_query(payload, '$.boxScoreTraditional.homeTeam') as team_json,
        observed_at
    from latest
    union all
    select
        json_value(payload, '$.boxScoreTraditional.gameId'),
        json_query(payload, '$.boxScoreTraditional.awayTeam'),
        observed_at
    from latest
)

select
    nba_game_id,
    safe_cast(json_value(team_json, '$.teamId') as int64) as nba_team_id,
    safe_cast(json_value(p, '$.personId') as int64) as nba_player_id,
    coalesce(json_value(p, '$.position'), '') != '' as is_starter,
    observed_at
from sides, unnest(json_query_array(team_json, '$.players')) as p
