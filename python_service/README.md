# Cricket Companion – Analytics Service

A **FastAPI** microservice that exposes cricket analytics endpoints by querying
the `cricket_companion` MySQL database.

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | ≥ 3.11 |
| MySQL | ≥ 8.0 (running, `cricket_companion` DB populated) |
| pip | latest |

---

## Quick Start

### 1 – Clone / navigate to the folder

```bash
cd cricket_companion/python_service
```

### 2 – Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3 – Install dependencies

```bash
pip install -r requirements.txt
```

### 4 – Configure environment variables

Copy the example file and edit it:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set your MySQL root password (leave blank if none):

```dotenv
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=cricket_companion
DB_PORT=3306
DEBUG=true
```

### 5 – Start the server

```bash
uvicorn main:app --reload
```

The service will be available at **http://localhost:8000**

---

## API Endpoints

### Health Check

```
GET /health
```

Returns `{"status": "ok"}` if the service is running.

---

### Player Career Statistics

```
GET /player/{id}/stats
```

Returns career batting and bowling statistics for a player.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Player ID from the `players` table |

**Example**

```bash
curl http://localhost:8000/player/1/stats
```

**Response**

```json
{
  "player": {
    "id": 1,
    "name": "Virat Kohli",
    "age": 35,
    "role": "Batsman",
    "team": "Royal Challengers Bangalore"
  },
  "matches_played": 12,
  "total_runs": 540,
  "total_balls_faced": 390,
  "total_wickets": 0,
  "batting_average": 45.0,
  "strike_rate": 138.46,
  "bowling_average": null,
  "highest_score": 82,
  "best_bowling": 0
}
```

---

### Player Form Predictor & Rolling Stats

```
GET /player/{id}/form
```

Calculates 5-match rolling averages, composite form rating, form trend (`improving`, `declining`, or `stable`), best recent score, and consistency index ($\sigma_{\text{runs}}$) for a player.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Player ID from the `players` table |

**Example**

```bash
curl http://localhost:8000/player/1/form
```

**Response**

```json
{
  "player_id": 1,
  "player_name": "Rohit Sharma",
  "matches_analyzed": 5,
  "current_form_score": 45.5,
  "form_trend": "improving",
  "best_recent_score": 85,
  "consistency_index": 22.45,
  "rolling_avg_runs": 65.0,
  "rolling_avg_wickets": 0.0,
  "recent_performances": [
    {
      "match_id": 1,
      "match_date": "2024-03-24",
      "runs_scored": 85,
      "balls_faced": 60,
      "wickets_taken": 0
    },
    {
      "match_id": 3,
      "match_date": "2024-03-28",
      "runs_scored": 45,
      "balls_faced": 32,
      "wickets_taken": 0
    }
  ]
}
```

---


### Team Win Rate

```
GET /team/{id}/winrate
```

Returns the win/loss record and win percentage for a team.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Team ID from the `teams` table |

**Example**

```bash
curl http://localhost:8000/team/1/winrate
```

**Response**

```json
{
  "team": {
    "id": 1,
    "team_name": "Mumbai Indians",
    "captain": "Rohit Sharma",
    "coach": "Mahela Jayawardene"
  },
  "matches_played": 14,
  "wins": 9,
  "losses": 5,
  "win_rate_pct": 64.29
}
```

---

### Head-to-Head Match Comparison

```
GET /match/compare?team1={id}&team2={id}
```

Compares two teams across all their head-to-head encounters.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team1` | integer | ID of the first team |
| `team2` | integer | ID of the second team |

**Example**

```bash
curl "http://localhost:8000/match/compare?team1=1&team2=2"
```

**Response**

```json
{
  "team1": {
    "team": { "id": 1, "team_name": "Mumbai Indians", "captain": "Rohit Sharma", "coach": "Mahela Jayawardene" },
    "wins": 6,
    "win_rate_pct": 60.0
  },
  "team2": {
    "team": { "id": 2, "team_name": "Chennai Super Kings", "captain": "MS Dhoni", "coach": "Stephen Fleming" },
    "wins": 4,
    "win_rate_pct": 40.0
  },
  "total_h2h_matches": 10,
  "draws": 0,
  "last_match_winner": "Mumbai Indians",
  "last_match_date": "2024-05-18"
}
```

---

### Win Probability Prediction

```
POST /predict/win
```

Predicts match win probability percentages for both chasing and defending teams based on the current match state.

**Request Body (JSON)**

| Field | Type | Validation Rules | Description |
|-------|------|------------------|-------------|
| `current_runs` | integer | `>= 0` | Current runs scored by chasing team |
| `wickets_fallen` | integer | `>= 0, <= 10` | Wickets lost by chasing team |
| `overs_completed` | float | `>= 0.0, <= 20.0` | Overs completed in 2nd innings |
| `target` | integer | `> 0` | Target runs to win match |
| `venue` | string | `min_length=1` | Match venue |
| `batting_team` | string | `min_length=1` | Team batting in 2nd innings |
| `bowling_team` | string | `min_length=1` | Team bowling in 2nd innings |

**Example Request**

```bash
curl -X POST "http://localhost:8000/predict/win" \
     -H "Content-Type: application/json" \
     -d '{
       "current_runs": 120,
       "wickets_fallen": 3,
       "overs_completed": 14.2,
       "target": 165,
       "venue": "Wankhede Stadium",
       "batting_team": "Mumbai Indians",
       "bowling_team": "Chennai Super Kings"
     }'
```

**Response**

```json
{
  "batting_team": {
    "team": "Mumbai Indians",
    "win_probability_pct": 80.5
  },
  "bowling_team": {
    "team": "Chennai Super Kings",
    "win_probability_pct": 19.5
  },
  "predicted_winner": "Mumbai Indians",
  "match_state": {
    "current_runs": 120,
    "wickets_fallen": 3,
    "overs_completed": 14.2,
    "target": 165,
    "venue": "Wankhede Stadium",
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings"
  }
}
```


---

## Interactive API Docs

Once the server is running, open these in your browser:

| UI | URL |
|----|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

---

## Project Structure

```
python_service/
├── main.py          # FastAPI app & lifespan (DB pool init/teardown)
├── routes.py        # All endpoint handlers
├── models.py        # Pydantic response schemas
├── database.py      # aiomysql connection pool
├── config.py        # Settings (reads .env)
├── requirements.txt # Python dependencies
├── .env.example     # Template environment file
└── README.md        # This file
```

---

## Running Without --reload (Production-like)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

> **Note**: `--workers` > 1 is only supported on Unix. On Windows, use a
> single worker or switch to `hypercorn`.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Access denied for user 'root'` | Check `DB_PASSWORD` in `.env` |
| `Unknown database 'cricket_companion'` | Run `database/create_tables.sql` and `load_ipl_data.py` first |
| `Can't connect to MySQL server` | Ensure MySQL is running on port 3306 |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the activated venv |
