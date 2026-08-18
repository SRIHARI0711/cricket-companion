import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Ensure python_service is on sys.path
service_dir = Path(__file__).parent.parent / "python_service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper Mock Objects for aiomysql Connection and Cursor
# ---------------------------------------------------------------------------
class DummyAsyncCursor:
    def __init__(self, fetchone_val=None, fetchall_val=None, fetchone_side_effect=None):
        self.fetchone_val = fetchone_val
        self.fetchall_val = fetchall_val or []
        self.fetchone_side_effect = fetchone_side_effect
        self.call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(self, query, params=None):
        pass

    async def fetchone(self):
        if self.fetchone_side_effect:
            val = self.fetchone_side_effect[self.call_count]
            self.call_count += 1
            return val
        return self.fetchone_val

    async def fetchall(self):
        return self.fetchall_val


class DummyAsyncConn:
    def __init__(self, dummy_cursor):
        self.dummy_cursor = dummy_cursor

    def cursor(self, dictionary=True):
        return self.dummy_cursor

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# ---------------------------------------------------------------------------
# 1. Health Check Endpoint Returns 200
# ---------------------------------------------------------------------------
def test_health_check_returns_200():
    """Test 1: Health check returns HTTP 200 OK and valid status object."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "analytics_service"


# ---------------------------------------------------------------------------
# 2. Player Stats Endpoint Returns Correct Schema
# ---------------------------------------------------------------------------
def test_player_stats_returns_correct_schema():
    """Test 2: Player stats endpoint returns correct PlayerStats schema."""
    mock_player_row = {
        "id": 1,
        "name": "Virat Kohli",
        "age": 35,
        "role": "Batsman",
        "team": "Royal Challengers Bangalore"
    }
    mock_stats_row = {
        "matches_played": 12,
        "total_runs": 540,
        "total_balls_faced": 390,
        "total_wickets": 0,
        "highest_score": 82,
        "best_bowling": 0
    }

    dummy_cursor = DummyAsyncCursor(fetchone_side_effect=[mock_player_row, mock_stats_row])

    with patch("routes.get_connection", return_value=DummyAsyncConn(dummy_cursor)):
        response = client.get("/player/1/stats")
        assert response.status_code == 200
        data = response.json()

        # Validate schema keys
        assert "player" in data
        assert data["player"]["id"] == 1
        assert data["player"]["name"] == "Virat Kohli"
        assert data["player"]["role"] == "Batsman"
        assert data["matches_played"] == 12
        assert data["total_runs"] == 540
        assert data["total_balls_faced"] == 390
        assert data["total_wickets"] == 0
        assert data["batting_average"] == 45.0
        assert data["strike_rate"] == 138.46
        assert data["highest_score"] == 82
        assert data["best_bowling"] == 0


# ---------------------------------------------------------------------------
# 3. Win Predictor Returns Probability Between 0 and 100
# ---------------------------------------------------------------------------
def test_win_predictor_returns_probability_between_0_and_100():
    """Test 3: Win predictor returns probability percentages between 0 and 100."""
    payload = {
        "batting_team": "Mumbai Indians",
        "bowling_team": "Chennai Super Kings",
        "current_runs": 120,
        "wickets_fallen": 3,
        "overs_completed": 14.2,
        "target": 180,
        "venue": "Wankhede Stadium"
    }
    response = client.post("/predict/win", json=payload)
    assert response.status_code == 200
    data = response.json()

    batting_prob = data["batting_team"]["win_probability_pct"]
    bowling_prob = data["bowling_team"]["win_probability_pct"]

    assert 0.0 <= batting_prob <= 100.0
    assert 0.0 <= bowling_prob <= 100.0
    assert round(batting_prob + bowling_prob, 1) == 100.0
    assert "predicted_winner" in data


# ---------------------------------------------------------------------------
# 4. Form Endpoint Returns Trend as One of Improving / Declining / Stable
# ---------------------------------------------------------------------------
def test_form_endpoint_returns_trend_as_improving_declining_or_stable():
    """Test 4: Form endpoint returns form_trend as one of improving, declining, or stable."""
    mock_player_row = {
        "id": 1,
        "name": "Rohit Sharma",
        "age": 37,
        "role": "Batsman",
        "team": "Mumbai Indians"
    }
    mock_scorecard_rows = [
        {"match_id": 10, "match_date": None, "runs_scored": 85, "balls_faced": 50, "wickets_taken": 0},
        {"match_id": 9, "match_date": None, "runs_scored": 65, "balls_faced": 40, "wickets_taken": 0},
        {"match_id": 8, "match_date": None, "runs_scored": 45, "balls_faced": 30, "wickets_taken": 0},
        {"match_id": 7, "match_date": None, "runs_scored": 25, "balls_faced": 20, "wickets_taken": 0},
        {"match_id": 6, "match_date": None, "runs_scored": 15, "balls_faced": 10, "wickets_taken": 0},
        {"match_id": 5, "match_date": None, "runs_scored": 10, "balls_faced": 8, "wickets_taken": 0},
    ]

    dummy_cursor = DummyAsyncCursor(fetchone_val=mock_player_row, fetchall_val=mock_scorecard_rows)

    with patch("routes.get_connection", return_value=DummyAsyncConn(dummy_cursor)):
        response = client.get("/player/1/form")
        assert response.status_code == 200
        data = response.json()

        assert "form_trend" in data
        assert data["form_trend"] in ["improving", "declining", "stable"]
        assert "current_form_score" in data
        assert "consistency_index" in data


# ---------------------------------------------------------------------------
# 5. Cluster Endpoint Returns All Players with a Cluster Label
# ---------------------------------------------------------------------------
def test_cluster_endpoint_returns_all_players_with_cluster_label():
    """Test 5: Player cluster endpoint returns players list with cluster labels."""
    mock_clusters_rows = [
        {
            "id": 1,
            "player_name": "Virat Kohli",
            "cluster_id": 0,
            "archetype_label": "Anchor / Elite Top-Order",
            "innings": 200,
            "total_runs": 7000,
            "strike_rate": 130.5,
            "batting_average": 38.5,
            "boundary_percentage": 52.0
        },
        {
            "id": 2,
            "player_name": "MS Dhoni",
            "cluster_id": 2,
            "archetype_label": "Middle-Order Finisher",
            "innings": 180,
            "total_runs": 5000,
            "strike_rate": 135.8,
            "batting_average": 39.0,
            "boundary_percentage": 55.0
        }
    ]

    dummy_cursor = DummyAsyncCursor(fetchall_val=mock_clusters_rows)

    with patch("routes.get_connection", return_value=DummyAsyncConn(dummy_cursor)):
        response = client.get("/clusters")
        assert response.status_code == 200
        data = response.json()

        assert "clusters" in data
        assert isinstance(data["clusters"], list)
        assert len(data["clusters"]) == 2

        for player_cluster in data["clusters"]:
            assert "player_name" in player_cluster
            assert "cluster_id" in player_cluster
            assert "archetype_label" in player_cluster
