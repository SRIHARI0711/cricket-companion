"""
Route handlers for the analytics endpoints.

Tables used (from cricket_companion schema):
  players    – id, name, age, role, team
  scorecards – player_id, match_id, runs_scored, balls_faced, wickets_taken
  matches    – id, team1_id, team2_id, winner_id, match_date
  teams      – id, team_name, captain, coach
"""

import os
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from database import get_connection
from models import (
    MatchCompareResponse,
    HeadToHeadRecord,
    PlayerInfo,
    PlayerStats,
    TeamInfo,
    TeamWinRate,
    WinPredictionRequest,
    WinPredictionResponse,
    TeamProbability,
)

router = APIRouter()

# Model loading helper
_model = None

def get_ml_model():
    global _model
    if _model is None:
        possible_paths = [
            Path(__file__).parent / "models" / "win_probability_model.pkl",
            Path("python_service/models/win_probability_model.pkl"),
            Path("models/win_probability_model.pkl"),
        ]
        model_path = None
        for p in possible_paths:
            if p.exists():
                model_path = p
                break

        if model_path is None:
            raise HTTPException(
                status_code=500,
                detail="Trained ML model (win_probability_model.pkl) not found. Run train_model.py first."
            )
        
        try:
            _model = joblib.load(model_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load trained model file: {str(e)}"
            )
    return _model



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


# ---------------------------------------------------------------------------
# POST /predict/win
# ---------------------------------------------------------------------------

TEAM_ALIASES = {
    "Delhi Daredevils":            "Delhi Capitals",
    "Deccan Chargers":             "Sunrisers Hyderabad",
    "Pune Warriors":               "Rising Pune Supergiant",
    "Rising Pune Supergiants":     "Rising Pune Supergiant",
    "Kings XI Punjab":             "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
}


def normalize_team_name(name: str) -> str:
    return TEAM_ALIASES.get(name.strip(), name.strip())


@router.post(
    "/predict/win",
    response_model=WinPredictionResponse,
    summary="Predict match win probability",
    description=(
        "Accepts current 2nd innings match state (runs, wickets, overs, target, "
        "venue, batting team, bowling team) and returns win probability percentage for both teams."
    ),
)
async def predict_win_probability(payload: WinPredictionRequest) -> WinPredictionResponse:
    if payload.batting_team.strip().lower() == payload.bowling_team.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="batting_team and bowling_team cannot be the same team"
        )

    model = get_ml_model()

    normalized_batting = normalize_team_name(payload.batting_team)
    normalized_bowling = normalize_team_name(payload.bowling_team)

    input_df = pd.DataFrame([{
        "current_runs": payload.current_runs,
        "wickets_fallen": payload.wickets_fallen,
        "overs_completed": payload.overs_completed,
        "target": payload.target,
        "venue": payload.venue,
        "batting_team": normalized_batting,
        "bowling_team": normalized_bowling,
    }])

    try:
        # Model predict_proba returns [prob(class 0: bowling team win), prob(class 1: batting team win)]
        probabilities = model.predict_proba(input_df)[0]
        prob_bowling_team = float(probabilities[0])
        prob_batting_team = float(probabilities[1])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )

    batting_win_pct = round(prob_batting_team * 100, 2)
    bowling_win_pct = round(prob_bowling_team * 100, 2)

    predicted_winner = payload.batting_team if batting_win_pct >= bowling_win_pct else payload.bowling_team

    return WinPredictionResponse(
        batting_team=TeamProbability(team=payload.batting_team, win_probability_pct=batting_win_pct),
        bowling_team=TeamProbability(team=payload.bowling_team, win_probability_pct=bowling_win_pct),
        predicted_winner=predicted_winner,
        match_state=payload,
    )

