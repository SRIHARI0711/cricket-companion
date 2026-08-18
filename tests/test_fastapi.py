import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure python_service is on sys.path
service_dir = Path(__file__).parent.parent / "python_service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns HTTP 200 OK and valid status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "analytics_service"


def test_win_prediction_validation_same_team():
    """Verify predict/win returns 400 Bad Request when batting and bowling teams are identical."""
    payload = {
        "batting_team": "Mumbai Indians",
        "bowling_team": "Mumbai Indians",
        "current_runs": 100,
        "wickets_fallen": 2,
        "overs_completed": 10.0,
        "target": 180,
        "venue": "Wankhede Stadium"
    }
    response = client.post("/predict/win", json=payload)
    assert response.status_code == 400
    assert "cannot be the same team" in response.json()["detail"]


def test_venues_endpoint():
    """Verify venues endpoint returns a valid response."""
    response = client.get("/venues")
    assert response.status_code == 200
    assert "venues" in response.json()
    assert isinstance(response.json()["venues"], list)
