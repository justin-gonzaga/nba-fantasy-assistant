-- DATA-038: every backfilled season has all 30 teams with pace, and at least 26 known head coaches
-- (the source lists none for a coach fired after the season: 10 of 341 team-seasons).
select season, count(*) as teams, countif(coach_id is not null) as coaches
from {{ ref('int_team_season_context') }}
where season between '2015-16' and '2025-26'
group by season
having count(*) != 30 or countif(pace is null) > 0 or countif(coach_id is not null) < 26
