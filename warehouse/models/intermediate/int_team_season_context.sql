-- Team context per team-season for ANL-010 (DATA-038): head coach (and whether he is new),
-- pace and ratings, and how concentrated the team's minutes and shots were among its top 3 players.
-- Every team-season comes from the team stats (30 a season); the coach can be missing: the source
-- lists no head coach for a team whose coach was fired after the season (10 of 341, 2015-16 → 2025-26).
with coach as (
    select
        season,
        nba_team_id,
        coach_id,
        coach_name
    from {{ ref('stg_nba_stats__head_coach') }}
),

player_totals as (
    select season, nba_team_id, nba_player_id, sum(minutes) as minutes, sum(fga) as fga
    from {{ ref('stg_nba_stats__player_game') }}
    group by 1, 2, 3
),

ranked as (
    select
        *,
        row_number() over (partition by season, nba_team_id order by minutes desc, nba_player_id) as minutes_rank,
        row_number() over (partition by season, nba_team_id order by fga desc, nba_player_id) as fga_rank
    from player_totals
),

concentration as (
    select
        season,
        nba_team_id,
        safe_divide(sum(if(minutes_rank <= 3, minutes, 0)), sum(minutes)) as minutes_top3_share,
        safe_divide(sum(if(fga_rank <= 3, fga, 0)), sum(fga)) as fga_top3_share
    from ranked
    group by 1, 2
)

select
    a.season,
    a.nba_team_id,
    c.coach_id,
    c.coach_name,
    p.coach_id as previous_coach_id,
    -- null when either season's coach is unknown (not "no change")
    if(c.coach_id is null or p.coach_id is null, null, c.coach_id != p.coach_id) as new_coach,
    a.pace,
    a.off_rating,
    a.def_rating,
    k.minutes_top3_share,
    k.fga_top3_share
from {{ ref('stg_nba_stats__team_season_advanced') }} as a
left join coach as c on c.season = a.season and c.nba_team_id = a.nba_team_id
left join coach as p
    on p.nba_team_id = a.nba_team_id
    and cast(substr(p.season, 1, 4) as int64) = cast(substr(a.season, 1, 4) as int64) - 1
left join concentration as k on k.season = a.season and k.nba_team_id = a.nba_team_id
