-- One row per player per regular season: totals and games from the game logs, age from the
-- season totals. Makes and attempts stay separate; percentages are derived later.
with games as (
    select
        season,
        nba_player_id,
        any_value(player_name having max game_date) as player_name,
        any_value(nba_team_id having min game_date) as first_nba_team_id,
        any_value(nba_team_id having max game_date) as last_nba_team_id,
        count(distinct nba_team_id) as teams_played_for,
        count(*) as games_played,
        sum(minutes) as minutes,
        sum(fgm) as fgm,
        sum(fga) as fga,
        sum(fg3m) as fg3m,
        sum(fg3a) as fg3a,
        sum(ftm) as ftm,
        sum(fta) as fta,
        sum(oreb) as oreb,
        sum(dreb) as dreb,
        sum(reb) as reb,
        sum(ast) as ast,
        sum(stl) as stl,
        sum(blk) as blk,
        sum(tov) as tov,
        sum(pts) as pts,
        min(game_date) as first_game_date,
        max(game_date) as last_game_date
    from {{ ref('stg_nba_stats__player_game') }}
    group by 1, 2
),

team_game_counts as (
    select season, nba_team_id, count(*) as team_games
    from {{ ref('stg_nba_stats__team_game') }}
    group by 1, 2
),

season_games as (
    select season, max(team_games) as season_team_games
    from team_game_counts
    group by 1
)

select
    g.season,
    cast(left(g.season, 4) as int64) as season_start_year,
    g.nba_player_id,
    g.player_name,
    g.first_nba_team_id,
    g.last_nba_team_id,
    g.teams_played_for,
    t.age,
    g.games_played,
    s.season_team_games,
    g.minutes,
    g.fgm, g.fga, g.fg3m, g.fg3a, g.ftm, g.fta,
    g.oreb, g.dreb, g.reb, g.ast, g.stl, g.blk, g.tov, g.pts,
    g.first_game_date,
    g.last_game_date
from games as g
left join {{ ref('stg_nba_stats__player_season_totals') }} as t using (season, nba_player_id)
left join season_games as s using (season)
