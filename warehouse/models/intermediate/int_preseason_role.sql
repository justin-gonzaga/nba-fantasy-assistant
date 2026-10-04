-- Pre-season role per player x season (DATA-030 / DRAFT-008): only exhibition games up to
-- 2 days before that season's opening night (the draft happens 2 days before the opener).
{%- set openers = var('opening_nights', {'2026-27': '2026-10-20'}) %}

with openers as (
    select season, min(game_date) as opening_night
    from {{ ref('stg_nba_stats__team_game') }}
    group by 1
    {%- for season, day in openers.items() %}
    union all select '{{ season }}', date '{{ day }}'
    {%- endfor %}
),

cutoff as (
    select season, date_sub(min(opening_night), interval 2 day) as last_game_date
    from openers
    group by 1
),

games as (
    select g.*, coalesce(s.is_starter, false) as is_starter
    from {{ ref('stg_nba_stats__preseason_player_game') }} as g
    join cutoff as c using (season)
    left join {{ ref('stg_nba_stats__preseason_starter') }} as s using (nba_game_id, nba_player_id)
    where g.game_date <= c.last_game_date
),

season_quality as (
    -- Box scores before 2017-18 list a position for 10+ players per team, so "starts" there are
    -- not real starts. Treat starts as missing when the league-wide start rate is implausible.
    select season, countif(is_starter) / count(*) between 0.25 and 0.45 as starts_reliable
    from games
    group by 1
),

team_minutes as (
    select season, nba_team_id, sum(minutes) as team_minutes
    from games
    group by 1, 2
)

select
    g.season,
    g.nba_player_id,
    any_value(g.nba_team_id having max g.game_date) as nba_team_id,
    count(*) as pre_games,
    sum(g.minutes) as pre_minutes,
    sum(g.minutes) / count(*) as pre_mpg,
    if(any_value(q.starts_reliable), countif(g.is_starter), null) as pre_starts,
    if(any_value(q.starts_reliable), countif(g.is_starter) / count(*), null) as pre_start_share,
    sum(g.minutes) / any_value(t.team_minutes having max g.game_date) as pre_team_minutes_share,
    max(g.game_date) as last_pre_game_date
from games as g
join team_minutes as t using (season, nba_team_id)
join season_quality as q using (season)
group by 1, 2
