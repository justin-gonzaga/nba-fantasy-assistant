-- DRAFT-008 AC1 / G-24 leakage test: no pre-season game used for a season may be later than
-- 2 days before that season's opening night (the draft happens 2 days before the opener).
-- Opening night = the first regular-season game; the 2026-27 value comes from the opening_nights var.
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
    select season, date_sub(min(opening_night), interval 2 day) as last_allowed
    from openers
    group by 1
)

select r.season, r.nba_player_id, r.last_pre_game_date, c.last_allowed
from {{ ref('int_preseason_role') }} as r
left join cutoff as c using (season)
where c.last_allowed is null or r.last_pre_game_date > c.last_allowed
