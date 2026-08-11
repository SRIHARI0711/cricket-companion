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
