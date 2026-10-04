-- Review finding: a pre-season with no opening-night date would silently drop all its games.
-- Fail loudly instead: every season with pre-season games needs a regular-season opener or a var entry.
{%- set openers = var('opening_nights', {'2026-27': '2026-10-20'}) %}
with seasons as (
    select distinct season from {{ ref('stg_nba_stats__preseason_player_game') }}
),

known as (
    select distinct season from {{ ref('stg_nba_stats__team_game') }}
    {%- for season, day in openers.items() %}
    union distinct select '{{ season }}'
    {%- endfor %}
)

select s.season
from seasons as s
left join known as k using (season)
where k.season is null
