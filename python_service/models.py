"""
Pydantic response models for the analytics endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Player stats – GET /player/{id}/stats
# ---------------------------------------------------------------------------

class PlayerInfo(BaseModel):
    id: int
    name: str
    age: Optional[int]
    role: str
    team: Optional[str]


class PlayerStats(BaseModel):
    player: PlayerInfo
    matches_played: int = Field(..., description="Total matches with a scorecard entry")
    total_runs: int
    total_balls_faced: int
    total_wickets: int
    batting_average: Optional[float] = Field(
        None, description="total_runs / matches_played; None when no matches played"
    )
    strike_rate: Optional[float] = Field(
        None, description="(total_runs / total_balls_faced) * 100; None when no balls faced"
    )
    bowling_average: Optional[float] = Field(
        None, description="total_runs_conceded / total_wickets; None when no wickets taken"
    )
    highest_score: int = Field(0, description="Best single-match runs tally")
    best_bowling: int = Field(0, description="Most wickets in a single match")


# ---------------------------------------------------------------------------
# Team win-rate – GET /team/{id}/winrate
# ---------------------------------------------------------------------------

class TeamInfo(BaseModel):
    id: int
    team_name: str
    captain: Optional[str]
    coach: Optional[str]


class TeamWinRate(BaseModel):
    team: TeamInfo
    matches_played: int
    wins: int
    losses: int
    win_rate_pct: float = Field(..., description="Percentage rounded to 2 decimal places")


class VenueRecord(BaseModel):
    venue: str
    total_matches: int
    wins: int
    win_pct: float


class TeamWinRateExtended(BaseModel):
    team: TeamInfo
    matches_played: int
    wins: int
    losses: int
    win_rate_pct: float
    batting_first_wins: int = 0
    fielding_first_wins: int = 0
    batting_first_matches: int = 0
    fielding_first_matches: int = 0
    venue_stats: list[VenueRecord] = []


# ---------------------------------------------------------------------------
# Head-to-head comparison – GET /match/compare?team1=&team2=
# ---------------------------------------------------------------------------

class HeadToHeadRecord(BaseModel):
    team: TeamInfo
    wins: int
    win_rate_pct: float


class MatchCompareResponse(BaseModel):
    team1: HeadToHeadRecord
    team2: HeadToHeadRecord
    total_h2h_matches: int
    draws: int = Field(0, description="Matches with no winner recorded")
    last_match_winner: Optional[str] = Field(
        None, description="Name of the team that won the most recent head-to-head match"
    )
    last_match_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Win probability prediction – POST /predict/win
# ---------------------------------------------------------------------------

class WinPredictionRequest(BaseModel):
    current_runs: int = Field(..., ge=0, description="Current runs scored by chasing team")
    wickets_fallen: int = Field(..., ge=0, le=10, description="Wickets fallen in 2nd innings (0-10)")
    overs_completed: float = Field(..., ge=0.0, le=20.0, description="Overs completed (0.0 to 20.0)")
    target: int = Field(..., gt=0, description="Target runs to win")
    venue: str = Field(..., min_length=1, description="Match venue name")
    batting_team: str = Field(..., min_length=1, description="Team batting in 2nd innings")
    bowling_team: str = Field(..., min_length=1, description="Team bowling in 2nd innings")


class TeamProbability(BaseModel):
    team: str
    win_probability_pct: float = Field(..., description="Win probability percentage rounded to 2 decimal places")


class WinPredictionResponse(BaseModel):
    batting_team: TeamProbability
    bowling_team: TeamProbability
    predicted_winner: str
    match_state: WinPredictionRequest


# ---------------------------------------------------------------------------
# Player form predictor – GET /player/{id}/form
# ---------------------------------------------------------------------------

class MatchPerformance(BaseModel):
    match_id: int
    match_date: Optional[str] = Field(None, description="Match date in YYYY-MM-DD format")
    runs_scored: int
    balls_faced: int
    wickets_taken: int


class PlayerFormResponse(BaseModel):
    player_id: int
    player_name: str
    matches_analyzed: int = Field(..., description="Number of recent matches analyzed (up to 5)")
    current_form_score: float = Field(..., description="Weighted rolling form rating")
    form_trend: str = Field(..., description="Form trend: 'improving', 'declining', or 'stable'")
    best_recent_score: int = Field(..., description="Highest runs scored in recent matches")
    consistency_index: float = Field(..., description="Standard deviation of recent runs (lower = more consistent)")
    rolling_avg_runs: float = Field(..., description="Rolling average runs across recent matches")
    rolling_avg_wickets: float = Field(..., description="Rolling average wickets across recent matches")
    recent_performances: list[MatchPerformance] = Field(..., description="Match-by-match breakdown")


# ---------------------------------------------------------------------------
# Generic error wrapper
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str


