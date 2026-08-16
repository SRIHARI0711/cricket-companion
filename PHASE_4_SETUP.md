# Analytics Page Setup (Phase 4, Implementation #11)

This guide documents the setup instructions and verification steps required for running the Analytics page features of Cricket Companion.

## Prerequisites

1. **Python FastAPI Analytics Service**:
   Run the FastAPI analytics service on port 8000:
   ```bash
   cd python_service
   uvicorn main:app --reload --port 8000
   ```

2. **ML Win Probability Model**:
   Ensure the ML model file is trained and available at `python_service/models/win_probability_model.pkl`:
   ```bash
   python train_model.py
   ```

3. **Player Clusters Table**:
   Ensure player clustering script has populated the `player_clusters` database table:
   ```bash
   python cluster_players.py
   ```

4. **Node.js Express Backend**:
   Start the Node.js Express server on port 5000:
   ```bash
   npm run dev
   ```

## Pre-Flight Endpoint Verification

Verify that services are running and accessible via the proxy server:

1. **FastAPI Health Check**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:5000/api/analytics/health
   ```

2. **Teams Endpoint**:
   ```bash
   curl http://localhost:5000/api/teams
   ```

3. **Team Win Rate Proxy**:
   ```bash
   curl http://localhost:5000/api/analytics/team/1/winrate
   ```

4. **Player Clusters Proxy**:
   ```bash
   curl http://localhost:5000/api/analytics/clusters
   ```

5. **Win Predictor Proxy**:
   ```bash
   curl -X POST http://localhost:5000/api/analytics/predict/win \
     -H "Content-Type: application/json" \
     -d "{\"batting_team\":\"Mumbai Indians\",\"bowling_team\":\"Chennai Super Kings\",\"current_runs\":120,\"wickets_fallen\":3,\"overs_completed\":14.2,\"target\":180,\"venue\":\"Wankhede Stadium\"}"
   ```
