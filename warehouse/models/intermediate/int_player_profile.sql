-- One row per rostered player for the profile season (default 2026-27, as of the latest
-- roster capture): team, position, age at mid-season, experience, draft pick, and whether
-- the team differs from the last team played for in the previous season.
{%- set season = var('profile_season', '2026-27') %}
{%- set midpoint = var('profile_season_midpoint', '2027-01-15') %}
{%- set previous = (season[:4] | int - 1) ~ '-' ~ season[2:4] %}

with roster as (
    select * from {{ ref('stg_nba_stats__roster') }}
    where season = '{{ season }}'
),

history as (
    select
        nba_player_id,
        count(*) as seasons_played,
        max(season) as last_season_played
    from {{ ref('int_player_season') }}
    where season < '{{ season }}'
    group by 1
),

previous_team as (
    select nba_player_id, last_nba_team_id as previous_nba_team_id
    from {{ ref('int_player_season') }}
    where season = '{{ previous }}'
),

draft as (
    select *
    from {{ ref('stg_nba_stats__draft_pick') }}
    qualify row_number() over (partition by nba_player_id order by draft_year desc) = 1
)

select
    r.season,
    r.nba_player_id,
    r.player_name,
    r.nba_team_id,
    r.nba_position,
    r.birth_date,
    round(date_diff(date '{{ midpoint }}', r.birth_date, day) / 365.25, 2) as age_at_midseason,
    r.experience_years,
    coalesce(h.seasons_played, 0) as seasons_played,
    h.last_season_played,
    p.previous_nba_team_id,
    p.previous_nba_team_id is not null and p.previous_nba_team_id != r.nba_team_id as changed_team,
    d.draft_year,
    d.overall_pick,
    d.round_number,
    r.how_acquired,
    r.observed_at as roster_observed_at
from roster as r
left join history as h using (nba_player_id)
left join previous_team as p using (nba_player_id)
left join draft as d using (nba_player_id)
