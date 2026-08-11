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
# Generic error wrapper
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
