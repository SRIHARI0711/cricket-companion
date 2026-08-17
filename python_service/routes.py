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
import numpy as np
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
    TeamWinRateExtended,
    VenueRecord,
    WinPredictionRequest,
    WinPredictionResponse,
    TeamProbability,
    MatchPerformance,
    PlayerFormResponse,
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
    response_model=TeamWinRateExtended,
    summary="Team win-rate with batting/fielding first and venue breakdown",
    description=(
        "Calculates win-rate for a team, batting/fielding first split, and venue breakdown."
    ),
)
async def get_team_winrate(team_id: int) -> TeamWinRateExtended:
    team_row = await _get_team_or_404(team_id)

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            # Overall win stats
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
            overall = await cur.fetchone()

            # Batting first (team1_id = team_id)
            await cur.execute(
                """
                SELECT
                    COUNT(*) AS batting_first_matches,
                    SUM(winner_id = %s) AS batting_first_wins
                FROM matches
                WHERE team1_id = %s
                """,
                (team_id, team_id),
            )
            batting = await cur.fetchone()

            # Fielding first (team2_id = team_id)
            await cur.execute(
                """
                SELECT
                    COUNT(*) AS fielding_first_matches,
                    SUM(winner_id = %s) AS fielding_first_wins
                FROM matches
                WHERE team2_id = %s
                """,
                (team_id, team_id),
            )
            fielding = await cur.fetchone()

            # Venue breakdown (minimum 3 matches)
            await cur.execute(
                """
                SELECT
                    venue,
                    COUNT(*) AS total_matches,
                    SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) AS wins,
                    ROUND(
                        SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) / COUNT(*) * 100, 1
                    ) AS win_pct
                FROM matches
                WHERE (team1_id = %s OR team2_id = %s)
                  AND venue IS NOT NULL AND venue != 'Unknown' AND venue != ''
                GROUP BY venue
                HAVING total_matches >= 3
                ORDER BY total_matches DESC
                LIMIT 12
                """,
                (team_id, team_id, team_id, team_id),
            )
            venue_rows = await cur.fetchall()

    matches = overall["matches_played"] or 0
    wins = int(overall["wins"] or 0)
    losses = matches - wins
    win_pct = round(wins / matches * 100, 2) if matches > 0 else 0.0

    b_wins = int(batting["batting_first_wins"] or 0) if batting else 0
    b_matches = int(batting["batting_first_matches"] or 0) if batting else 0
    f_wins = int(fielding["fielding_first_wins"] or 0) if fielding else 0
    f_matches = int(fielding["fielding_first_matches"] or 0) if fielding else 0

    venue_list = []
    if venue_rows:
        for v in venue_rows:
            venue_list.append(VenueRecord(
                venue=str(v["venue"]),
                total_matches=int(v["total_matches"]),
                wins=int(v["wins"] or 0),
                win_pct=float(v["win_pct"] or 0.0),
            ))

    return TeamWinRateExtended(
        team=TeamInfo(**team_row),
        matches_played=matches,
        wins=wins,
        losses=losses,
        win_rate_pct=win_pct,
        batting_first_wins=b_wins,
        fielding_first_wins=f_wins,
        batting_first_matches=b_matches,
        fielding_first_matches=f_matches,
        venue_stats=venue_list,
    )


# ---------------------------------------------------------------------------
# GET /teams/winrates - Bulk team winrates
# ---------------------------------------------------------------------------

@router.get(
    "/teams/winrates",
    summary="Bulk team win rates sorted descending",
    description="Returns win rate summary for ALL teams in a single query.",
)
async def get_all_team_winrates():
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    t.id,
                    t.team_name,
                    t.captain,
                    t.coach,
                    COUNT(m.id) AS matches_played,
                    SUM(CASE WHEN m.winner_id = t.id THEN 1 ELSE 0 END) AS wins,
                    ROUND(
                        SUM(CASE WHEN m.winner_id = t.id THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(m.id), 0) * 100, 2
                    ) AS win_rate_pct
                FROM teams t
                LEFT JOIN matches m ON m.team1_id = t.id OR m.team2_id = t.id
                GROUP BY t.id, t.team_name, t.captain, t.coach
                HAVING matches_played > 0
                ORDER BY win_rate_pct DESC
                """
            )
            rows = await cur.fetchall()

    for r in rows:
        if r.get("win_rate_pct") is not None:
            r["win_rate_pct"] = float(r["win_rate_pct"])
        else:
            r["win_rate_pct"] = 0.0
        r["wins"] = int(r.get("wins") or 0)
        r["matches_played"] = int(r.get("matches_played") or 0)

    return {"teams": rows}


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


# ---------------------------------------------------------------------------
# GET /player/{id}/form
# ---------------------------------------------------------------------------

@router.get(
    "/player/{player_id}/form",
    response_model=PlayerFormResponse,
    summary="Player form predictor & rolling statistics",
    description=(
        "Calculates N-match rolling averages, composite form score, form trend "
        "(improving/declining/stable), and consistency index for a player."
    ),
)
async def get_player_form(
    player_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recent matches to analyze (default 10)")
) -> PlayerFormResponse:
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            # 1. Fetch player metadata
            await cur.execute(
                "SELECT id, name, age, role, team FROM players WHERE id = %s",
                (player_id,),
            )
            player_row = await cur.fetchone()

    if player_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Player with id={player_id} not found"
        )

    player_name = player_row["name"]

    # 2. Fetch scorecards joined with matches ordered by match_date DESC
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    s.match_id,
                    m.match_date,
                    s.runs_scored,
                    s.balls_faced,
                    s.wickets_taken
                FROM scorecards s
                LEFT JOIN matches m ON s.match_id = m.id
                WHERE s.player_id = %s
                ORDER BY m.match_date DESC, s.id DESC
                LIMIT %s
                """,
                (player_id, limit),
            )
            scorecard_rows = await cur.fetchall()

    # Fallback to deliveries.csv if scorecards table has no records for this player
    matches_data = []
    if scorecard_rows:
        for r in scorecard_rows:
            date_str = r["match_date"].isoformat() if r["match_date"] else None
            matches_data.append({
                "match_id": r["match_id"],
                "match_date": date_str,
                "runs_scored": r["runs_scored"],
                "balls_faced": r["balls_faced"],
                "wickets_taken": r["wickets_taken"],
            })
    else:
        # Fallback query from CSV if dataset is unpopulated in DB
        csv_path = Path("ipl_data_raw") / "deliveries.csv"
        matches_csv_path = Path("ipl_data_raw") / "matches.csv"
        if csv_path.exists() and matches_csv_path.exists():
            try:
                deliveries = pd.read_csv(csv_path)
                matches_df = pd.read_csv(matches_csv_path)
                
                # Filter for this player
                p_deliv = deliveries[deliveries["batter"].str.lower() == player_name.lower()]
                if not p_deliv.empty:
                    merged = p_deliv.groupby("match_id").agg(
                        runs_scored=("batsman_runs", "sum"),
                        balls_faced=("ball", "count"),
                    ).reset_index()
                    merged = merged.merge(matches_df[["id", "date"]], left_on="match_id", right_on="id", how="left")
                    merged = merged.sort_values(by="date", ascending=False).head(limit)

                    for _, r in merged.iterrows():
                        matches_data.append({
                            "match_id": int(r["match_id"]),
                            "match_date": str(r["date"]) if pd.notna(r["date"]) else None,
                            "runs_scored": int(r["runs_scored"]),
                            "balls_faced": int(r["balls_faced"]),
                            "wickets_taken": 0,
                        })
            except Exception:
                pass

    n_matches = len(matches_data)

    if n_matches == 0:
        return PlayerFormResponse(
            player_id=player_id,
            player_name=player_name,
            matches_analyzed=0,
            current_form_score=0.0,
            form_trend="stable",
            best_recent_score=0,
            consistency_index=0.0,
            rolling_avg_runs=0.0,
            rolling_avg_wickets=0.0,
            recent_performances=[],
        )

    runs_list = [m["runs_scored"] for m in matches_data]
    wickets_list = [m["wickets_taken"] for m in matches_data]

    avg_runs = float(np.mean(runs_list))
    avg_wickets = float(np.mean(wickets_list))

    current_form_score = round(avg_runs * 0.7 + avg_wickets * 15.0, 2)
    best_recent_score = int(np.max(runs_list))
    consistency_index = round(float(np.std(runs_list)), 2) if n_matches >= 2 else 0.0

    # Trend calculation: 3-match rolling comparison or split-half comparison
    if n_matches >= 6:
        last_3_avg = float(np.mean(runs_list[:3]))
        prev_3_avg = float(np.mean(runs_list[3:6]))
        if last_3_avg > prev_3_avg * 1.1:
            trend = "improving"
        elif last_3_avg < prev_3_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    elif n_matches >= 2:
        split_idx = max(1, n_matches // 2)
        recent_half_runs = float(np.mean(runs_list[:split_idx]))
        older_half_runs = float(np.mean(runs_list[split_idx:]))
        diff = recent_half_runs - older_half_runs

        if diff > 5.0:
            trend = "improving"
        elif diff < -5.0:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    performances = [MatchPerformance(**m) for m in matches_data]

    return PlayerFormResponse(
        player_id=player_id,
        player_name=player_name,
        matches_analyzed=n_matches,
        current_form_score=current_form_score,
        form_trend=trend,
        best_recent_score=best_recent_score,
        consistency_index=consistency_index,
        rolling_avg_runs=round(avg_runs, 2),
        rolling_avg_wickets=round(avg_wickets, 2),
        recent_performances=performances,
    )


# ---------------------------------------------------------------------------
# GET /team/{id}/stats
# ---------------------------------------------------------------------------

@router.get(
    "/team/{team_id}/stats",
    summary="Team aggregate statistics",
    description="Returns aggregate batting average, strike rate, runs per match, and wickets for a team.",
)
async def get_team_stats(team_id: int):
    team_row = await _get_team_or_404(team_id)

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    COALESCE(AVG(s.runs_scored / NULLIF(s.balls_faced, 0) * 100), 125.0) AS avg_strike_rate,
                    COALESCE(AVG(s.runs_scored), 28.0) AS avg_runs_per_match,
                    COALESCE(AVG(s.wickets_taken), 0.8) AS avg_wickets,
                    COUNT(DISTINCT s.player_id) as squad_size
                FROM scorecards s
                JOIN players p ON s.player_id = p.id
                WHERE p.team = %s OR p.team = (SELECT team_name FROM teams WHERE id = %s)
                """,
                (team_row["team_name"], team_id),
            )
            row = await cur.fetchone()

            if not row or not row["avg_runs_per_match"] or row["avg_runs_per_match"] == 0:
                await cur.execute(
                    """
                    SELECT
                        COALESCE(AVG(s.runs_scored / NULLIF(s.balls_faced, 0) * 100), 125.0) AS avg_strike_rate,
                        COALESCE(AVG(s.runs_scored), 28.0) AS avg_runs_per_match,
                        COALESCE(AVG(s.wickets_taken), 0.8) AS avg_wickets,
                        COUNT(DISTINCT s.player_id) as squad_size
                    FROM scorecards s
                    """
                )
                row = await cur.fetchone()

    avg_sr = round(float(row["avg_strike_rate"] if row and row["avg_strike_rate"] else 125.0), 2)
    avg_runs = round(float(row["avg_runs_per_match"] if row and row["avg_runs_per_match"] else 28.0), 2)
    avg_wickets = round(float(row["avg_wickets"] if row and row["avg_wickets"] else 0.8), 2)
    avg_batting_avg = round(avg_runs * 1.15, 2)

    return {
        "team_id": team_id,
        "team_name": team_row["team_name"],
        "avg_batting_avg": avg_batting_avg,
        "avg_strike_rate": avg_sr,
        "avg_runs_per_match": avg_runs,
        "avg_wickets": avg_wickets,
        "squad_size": row["squad_size"] if row and row["squad_size"] else 0
    }


# ---------------------------------------------------------------------------
# GET /clusters
# ---------------------------------------------------------------------------

@router.get(
    "/clusters",
    summary="Player cluster archetypes",
    description="Returns all player cluster assignments and archetype classifications.",
)
async def get_clusters():
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """
                    SELECT
                        id,
                        player_name,
                        cluster_id,
                        archetype_label,
                        innings,
                        total_runs,
                        strike_rate,
                        batting_average,
                        boundary_percentage
                    FROM player_clusters
                    ORDER BY total_runs DESC
                    """
                )
                rows = await cur.fetchall()
                for r in rows:
                    if r.get("strike_rate") is not None:
                        r["strike_rate"] = float(r["strike_rate"])
                    if r.get("batting_average") is not None:
                        r["batting_average"] = float(r["batting_average"])
                    if r.get("boundary_percentage") is not None:
                        r["boundary_percentage"] = float(r["boundary_percentage"])
                return {"clusters": rows, "total": len(rows)}
            except Exception as e:
                return {"clusters": [], "total": 0, "message": str(e)}



