-- DATA-029 AC2: player points summed per team-game equal the team log's points.
-- Returns the mismatching team-games (the test passes when none are returned).
with players as (
    select nba_game_id, nba_team_id, sum(pts) as player_pts
    from {{ ref('stg_nba_stats__player_game') }}
    group by 1, 2
)

select t.season, t.nba_game_id, t.nba_team_id, t.pts as team_pts, p.player_pts
from {{ ref('stg_nba_stats__team_game') }} as t
left join players as p using (nba_game_id, nba_team_id)
where p.player_pts is null or p.player_pts != t.pts
