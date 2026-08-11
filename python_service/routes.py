"""
Route handlers for the analytics endpoints.

Tables used (from cricket_companion schema):
  players    – id, name, age, role, team
  scorecards – player_id, match_id, runs_scored, balls_faced, wickets_taken
  matches    – id, team1_id, team2_id, winner_id, match_date
  teams      – id, team_name, captain, coach
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from database import get_connection
from models import (
    MatchCompareResponse,
    HeadToHeadRecord,
    PlayerInfo,
    PlayerStats,
    TeamInfo,
    TeamWinRate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper – fetch a team row or raise 404
# ---------------------------------------------------------------------------

async def _get_team_or_404(team_id: int) -> dict:
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, team_name, captain, coach FROM teams WHERE id = %s",
                (team_id,),
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Team with id={team_id} not found")
    return row


# ---------------------------------------------------------------------------
# GET /player/{id}/stats
# ---------------------------------------------------------------------------

@router.get(
    "/player/{player_id}/stats",
    response_model=PlayerStats,
    summary="Player career statistics",
    description=(
        "Returns career batting and bowling statistics for a single player "
        "aggregated across all scorecards in the database."
    ),
)
async def get_player_stats(player_id: int) -> PlayerStats:
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            # --- fetch player meta ---
            await cur.execute(
                "SELECT id, name, age, role, team FROM players WHERE id = %s",
                (player_id,),
            )
            player_row = await cur.fetchone()
            if player_row is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Player with id={player_id} not found",
                )

            # --- aggregate scorecard data ---
            await cur.execute(
                """
                SELECT
                    COUNT(*)            AS matches_played,
                    COALESCE(SUM(runs_scored),  0) AS total_runs,
                    COALESCE(SUM(balls_faced),  0) AS total_balls_faced,
                    COALESCE(SUM(wickets_taken),0) AS total_wickets,
                    COALESCE(MAX(runs_scored),  0) AS highest_score,
                    COALESCE(MAX(wickets_taken),0) AS best_bowling
                FROM scorecards
                WHERE player_id = %s
                """,
                (player_id,),
            )
            stats = await cur.fetchone()

    matches = stats["matches_played"]
    runs    = stats["total_runs"]
    balls   = stats["total_balls_faced"]
    wkts    = stats["total_wickets"]

    batting_avg   = round(runs / matches, 2)    if matches > 0 else None
    strike_rate   = round(runs / balls * 100, 2) if balls   > 0 else None
    # bowling_average = runs conceded by the bowler / wickets taken
    # (we track runs_scored per player; for bowling we use runs_scored as proxy
    #  for runs conceded when the player took wickets)
    bowling_avg   = round(runs / wkts, 2)       if wkts    > 0 else None

    return PlayerStats(
        player=PlayerInfo(**player_row),
        matches_played=matches,
        total_runs=runs,
        total_balls_faced=balls,
        total_wickets=wkts,
        batting_average=batting_avg,
        strike_rate=strike_rate,
        bowling_average=bowling_avg,
        highest_score=stats["highest_score"],
        best_bowling=stats["best_bowling"],
    )


# ---------------------------------------------------------------------------
# GET /team/{id}/winrate
# ---------------------------------------------------------------------------

@router.get(
    "/team/{team_id}/winrate",
    response_model=TeamWinRate,
    summary="Team win-rate",
    description=(
        "Calculates win-rate for a team across all matches where the team "
        "appears as team1 or team2."
    ),
)
async def get_team_winrate(team_id: int) -> TeamWinRate:
    team_row = await _get_team_or_404(team_id)

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    COUNT(*) AS matches_played,
                    SUM(winner_id = %s) AS wins
                FROM matches
                WHERE team1_id = %s OR team2_id = %s
                """,
                (team_id, team_id, team_id),
            )
            row = await cur.fetchone()

    matches = row["matches_played"] or 0
    wins    = int(row["wins"] or 0)
    losses  = matches - wins
    win_pct = round(wins / matches * 100, 2) if matches > 0 else 0.0

    return TeamWinRate(
        team=TeamInfo(**team_row),
        matches_played=matches,
        wins=wins,
        losses=losses,
        win_rate_pct=win_pct,
    )


# ---------------------------------------------------------------------------
# GET /match/compare?team1={id}&team2={id}
# ---------------------------------------------------------------------------

@router.get(
    "/match/compare",
    response_model=MatchCompareResponse,
    summary="Head-to-head team comparison",
    description=(
        "Compares two teams across all head-to-head matches and returns win "
        "counts, win percentages, and the result of the most recent encounter."
    ),
)
async def compare_teams(
    team1: int = Query(..., description="ID of the first team"),
    team2: int = Query(..., description="ID of the second team"),
) -> MatchCompareResponse:
    if team1 == team2:
        raise HTTPException(
            status_code=400, detail="team1 and team2 must be different"
        )

    # Validate both teams exist
    team1_row = await _get_team_or_404(team1)
    team2_row = await _get_team_or_404(team2)

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            # All head-to-head matches (in either direction)
            await cur.execute(
                """
                SELECT
                    id,
                    winner_id,
                    match_date
                FROM matches
                WHERE (team1_id = %s AND team2_id = %s)
                   OR (team1_id = %s AND team2_id = %s)
                ORDER BY match_date DESC
                """,
                (team1, team2, team2, team1),
            )
            h2h_matches = await cur.fetchall()

            # Latest winner name (if any)
            last_winner: Optional[str] = None
            last_date:   Optional[str] = None

            if h2h_matches:
                latest = h2h_matches[0]
                last_date = (
                    latest["match_date"].isoformat()
                    if latest["match_date"] else None
                )
                if latest["winner_id"]:
                    await cur.execute(
                        "SELECT team_name FROM teams WHERE id = %s",
                        (latest["winner_id"],),
                    )
                    winner_row = await cur.fetchone()
                    last_winner = winner_row["team_name"] if winner_row else None

    total  = len(h2h_matches)
    wins1  = sum(1 for m in h2h_matches if m["winner_id"] == team1)
    wins2  = sum(1 for m in h2h_matches if m["winner_id"] == team2)
    draws  = total - wins1 - wins2

    win_pct1 = round(wins1 / total * 100, 2) if total > 0 else 0.0
    win_pct2 = round(wins2 / total * 100, 2) if total > 0 else 0.0

    return MatchCompareResponse(
        team1=HeadToHeadRecord(team=TeamInfo(**team1_row), wins=wins1, win_rate_pct=win_pct1),
        team2=HeadToHeadRecord(team=TeamInfo(**team2_row), wins=wins2, win_rate_pct=win_pct2),
        total_h2h_matches=total,
        draws=draws,
        last_match_winner=last_winner,
        last_match_date=last_date,
    )
