# 🏏 Cricket Companion & Analytics Engine

A comprehensive full-stack cricket management platform and machine learning analytics engine built for **IPL T20 Cricket**. The platform combines a robust **Node.js Express & MySQL** relational database backend with a **Python FastAPI** microservice powered by **scikit-learn** and **XGBoost** machine learning models.

---

## 🌟 Key Features

- **🏏 Complete Cricket Management (CRUD)**: Full management system for Teams, Players, Series, Matches, and Scorecards with dark/light theme web interface.
- **🔮 Live Win Probability Predictor**: 2nd-innings match outcome forecasting using an **XGBoost Classifier** trained on historical IPL ball-by-ball delivery datasets.
- **📊 Player Archetype Clustering**: Unsupervised **K-Means Clustering** ($k=5$) identifying T20 player roles (*Anchor*, *Power Hitter*, *Finisher*, *Accumulator*, *Tailender*).
- **📈 Player Form & Rolling Stats**: 5/10-match rolling averages, composite form rating score, form trend indicators (*Improving*, *Declining*, *Stable*), and performance consistency index ($\sigma$).
- **⚔️ Head-to-Head & Venue Analytics**: Deep-dive team comparisons and venue-specific win/loss percentages split by batting first vs. fielding first.

---

## 📐 System Architecture & Tech Stack

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND CLIENT                                   |
|                      HTML5  |  CSS3 (Custom Utility & Themes)                     |
|                   Vanilla JavaScript  |  Interactive Analytics UI                 |
+------------------------------------------+----------------------------------------+
                                           |
                                     HTTP / REST API
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                             NODE.JS EXPRESS BACKEND                               |
|                                  (Port 5000)                                      |
|  +-----------------------------------+  +--------------------------------------+  |
|  |     Core CRUD API Gateway         |  |      Analytics Proxy Controller      |  |
|  |  /api/players    /api/teams       |  |     /api/analytics/predict/win       |  |
|  |  /api/series     /api/matches     |  |     /api/analytics/player/:id/form   |  |
|  |  /api/scorecards                  |  |     /api/analytics/clusters          |  |
|  +-----------------+-----------------+  +------------------+-------------------+  |
+--------------------|---------------------------------------|----------------------+
                     |                                       |
                mysql2 Pool                            Axios HTTP Proxy
                     |                                       |
                     v                                       v
+--------------------------------------+  +-----------------------------------------+
|            MYSQL DATABASE            |  |         PYTHON FASTAPI SERVICE          |
|             (Port 3306)              |  |               (Port 8000)               |
|  +--------------------------------+  |  |  +-----------------------------------+  |
|  | Schema: cricket_companion      |  |  |  | Async Database Connection         |  |
|  |  - players       - teams       | <+--+--|  | (aiomysql Connection Pool)        |  |
|  |  - series        - matches     |  |  |  +-----------------------------------+  |
|  |  - scorecards    - clusters    |  |  |  | ML Inference & Analytics Routes   |  |
|  |  - ipl_batting_stats           |  |  |  |  - /predict/win   - /clusters     |  |
|  +--------------------------------+  |  |  |  - /player/form   - /match/compare|  |
+--------------------------------------+  |  +-----------------+-----------------+  |
                                          +--------------------|--------------------+
                                                               |
                                                          joblib Load
                                                               |
                                                               v
                                          +-----------------------------------------+
                                          |          ML MODEL ARTIFACTS             |
                                          |  - win_probability_model.pkl (XGBoost)  |
                                          |  - K-Means Clustering Pipelines         |
                                          +-----------------------------------------+
```

### Stack Summary

- **Frontend**: HTML5, Vanilla CSS3 (Custom design system with dark/light mode), JavaScript (ES6+).
- **Node.js Backend**: Node.js, Express.js, `mysql2`, `cors`, `dotenv`, `axios`.
- **Python Service**: Python 3.11+, FastAPI, `uvicorn`, `aiomysql`, `pydantic`, `joblib`.
- **Machine Learning & Data Science**: `scikit-learn`, `XGBoost`, `pandas`, `numpy`.
- **Database**: MySQL 8.0 Server.

---

## 🚀 How to Run

### Prerequisites

Ensure you have the following installed on your machine:
- **Node.js**: v14.0 or higher
- **Python**: v3.11 or higher
- **MySQL Server**: v8.0 or higher

---

### Step 1: Environment & Database Configuration

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SRIHARI0711/cricket-companion.git
   cd cricket-companion
   ```

2. **Create Root Environment File `.env`**:
   ```dotenv
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=cricket_companion
   DB_PORT=3306
   PORT=5000
   FASTAPI_URL=http://localhost:8000
   ```

3. **Initialize Database Tables & Seed Data**:
   ```bash
   npm run setup-db
   ```

---

### Step 2: Running Node.js Express Backend & Frontend (Port 5000)

1. **Install Node.js Dependencies**:
   ```bash
   npm install
   ```

2. **Start the Express Server**:
   ```bash
   # Development mode (with auto-restart)
   npm run dev

   # Production mode
   npm start
   ```

3. **Access Application**:
   Open browser at **http://localhost:5000**  
   - Default Login Credentials: `Username: admin` | `Password: cricket123`

---

### Step 3: Running Python FastAPI Service & ML Pipeline (Port 8000)

1. **Navigate to Python Service Directory**:
   ```bash
   cd python_service
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Python Service `.env`**:
   ```dotenv
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=cricket_companion
   DB_PORT=3306
   DEBUG=true
   ```

5. **Train ML Win Probability Model & Execute Player Clustering**:
   ```bash
   # Return to root directory
   cd ..

   # 1. Load Raw IPL Ball-by-Ball Data into MySQL
   python load_ipl_data.py

   # 2. Train XGBoost Win Probability Model
   python train_model.py

   # 3. Perform K-Means Player Clustering
   python cluster_players.py
   ```

6. **Launch FastAPI Analytics Service**:
   ```bash
   cd python_service
   uvicorn main:app --reload --port 8000
   ```

7. **Interactive API Documentation**:
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

---

## 🔌 API Documentation

### 1. Node.js Express Core CRUD Endpoints (`http://localhost:5000/api`)

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Players** | `GET` | `/api/players` | Retrieve all registered players |
| | `GET` | `/api/players/:id` | Retrieve single player details |
| | `POST` | `/api/players` | Create a new player profile |
| | `PUT` | `/api/players/:id` | Update existing player profile |
| | `DELETE` | `/api/players/:id` | Remove player profile |
| **Teams** | `GET` | `/api/teams` | Retrieve all teams |
| | `GET` | `/api/teams/:id` | Retrieve team by ID |
| | `POST` | `/api/teams` | Add a new team |
| | `PUT` | `/api/teams/:id` | Update team details |
| | `DELETE` | `/api/teams/:id` | Delete team |
| **Series** | `GET` | `/api/series` | Retrieve all series |
| | `GET` | `/api/series/:id` | Retrieve series by ID |
| | `POST` | `/api/series` | Create a new series |
| | `PUT` | `/api/series/:id` | Update series details |
| | `DELETE` | `/api/series/:id` | Delete series |
| **Matches** | `GET` | `/api/matches` | Retrieve all matches with team names |
| | `GET` | `/api/matches/:id` | Retrieve match by ID |
| | `POST` | `/api/matches` | Schedule a new match |
| | `PUT` | `/api/matches/:id` | Update match information |
| | `DELETE` | `/api/matches/:id` | Delete match |
| **Scorecards**| `GET` | `/api/scorecards` | Retrieve all scorecard entries |
| | `GET` | `/api/scorecards/:id` | Retrieve scorecard by ID |
| | `POST` | `/api/scorecards` | Add new scorecard record |
| | `PUT` | `/api/scorecards/:id` | Update scorecard entry |
| | `DELETE` | `/api/scorecards/:id` | Delete scorecard entry |

---

### 2. Node.js Analytics Proxy Gateway (`http://localhost:5000/api/analytics`)

| Method | Endpoint | Proxy Target | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/analytics/health` | `GET /health` | Service health status check |
| `GET` | `/api/analytics/player/:id/stats` | `GET /player/{id}/stats` | Fetch player career statistics |
| `POST` | `/api/analytics/predict/win` | `POST /predict/win` | Predict match win probability |
| `GET` | `/api/analytics/player/:id/form` | `GET /player/{id}/form` | Calculate player form rating & trend |
| `GET` | `/api/analytics/team/:id/stats` | `GET /team/{id}/stats` | Aggregate team batting/bowling statistics |
| `GET` | `/api/analytics/teams/winrates` | `GET /teams/winrates` | Bulk team winrates sorted descending |
| `GET` | `/api/analytics/team/:id/winrate` | `GET /team/{id}/winrate` | Team winrate & venue breakdown |
| `GET` | `/api/analytics/match/compare` | `GET /match/compare` | Head-to-head match comparison |
| `GET` | `/api/analytics/clusters` | `GET /clusters` | Player K-Means cluster archetypes |
| `GET` | `/api/analytics/venues` | `GET /venues` | Distinct match venues list |

---

### 3. Python FastAPI Native Endpoints (`http://localhost:8000`)

| Method | Endpoint | Request Body / Query Params | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | Returns `{"status": "ok"}` |
| `GET` | `/player/{id}/stats` | `id` (path) | Aggregated career stats across scorecards |
| `GET` | `/player/{id}/form` | `id` (path), `limit` (query) | $N$-match rolling stats, form score, trend |
| `GET` | `/team/{id}/winrate` | `id` (path) | Overall winrate + batting/fielding first split |
| `GET` | `/teams/winrates` | None | Win rates for all teams |
| `GET` | `/match/compare` | `team1`, `team2` (query) | Head-to-head stats & last winner |
| `POST` | `/predict/win` | JSON payload (match state) | XGBoost win probability prediction |
| `GET` | `/team/{id}/stats` | `id` (path) | Squad aggregate averages |
| `GET` | `/clusters` | None | All assigned player clusters & archetypes |
| `GET` | `/venues` | None | Venue names from training dataset |

---

## 🤖 ML Model Performance & Accuracy Metrics

The win probability model was trained on historical IPL 2nd-innings delivery data comprising **125,714 delivery samples** (across 1,095 matches and 260,920 raw delivery records), split into 100,571 training samples and 25,143 test samples.

### Win Probability Model Comparison

| Metric | Logistic Regression | XGBoost Classifier (Selected Best) |
| :--- | :---: | :---: |
| **Test Accuracy** | `80.26%` | **`88.06%`** |
| **Precision (Chasing Team Win)** | `0.8047` | **`0.8674`** |
| **Recall (Chasing Team Win)** | `0.8190` | **`0.9093`** |
| **F1-Score (Chasing Team Win)** | `0.8118` | **`0.8879`** |

> **Conclusion**: The **XGBoost Classifier** significantly outperformed Logistic Regression by **+7.80 percentage points** in test accuracy ($88.06\%$ vs $80.26\%$) and demonstrated a significantly higher recall ($90.93\%$), effectively modeling non-linear T20 match situations during 2nd-innings chases.

---

## 💡 Data Science Decisions

### 1. Why XGBoost over Logistic Regression for Win Probability

- **Non-Linear Match State Dynamics**: In T20 cricket, the relationship between runs required, overs completed, and wickets lost is inherently non-linear and conditional. For example, needing 50 runs off 30 balls with 8 wickets in hand represents an advantageous position (~85% win probability), whereas needing 50 runs off 30 balls with 8 wickets lost represents a desperate situation (~20% win probability). 
- **Higher-Order Feature Interactions**: A linear model (Logistic Regression) calculates fixed additive weights for features unless interaction terms are manually specified. XGBoost automatically constructs decision tree splits that naturally model high-order feature interactions like `(overs_completed * wickets_fallen)` and `(required_run_rate * venue_factor)`.
- **Handling High-Cardinality Categoricals**: XGBoost handles high-cardinality categorical features (`venue`, `batting_team`, `bowling_team`) efficiently without over-fitting or sensitivity to collinearity.

---

### 2. K-Means Cluster Count Selection ($k=5$)

- **Elbow Method Inertia Analysis**: We evaluated $k \in [2, 8]$ using the sum of squared distances (inertia). The elbow curve displayed a sharp inflection point at **$k = 5$**, after which inertia reduction plateaued.
- **Domain Interpretation**: In T20 cricket, batting statistics (total runs, strike rate, average, boundary %, innings) map cleanly into **5 distinct player archetypes**:
  1. **Anchor / Elite Top-Order**: High run tally, high average ($>35$), high innings count, stable strike rate.
  2. **Aggressive Opener / Power Hitter**: Extremely high strike rate ($>140$), high boundary percentage ($>60\%$), high run volume.
  3. **Middle-Order Finisher**: High strike rate ($>140$), lower innings count, high boundary percentage, medium average.
  4. **Middle-Order Accumulator**: Moderate average ($25-35$), moderate strike rate ($110-130$), lower boundary percentage.
  5. **Lower-Order / Tailender**: Low run volume, low average, minimal innings count.
- **Deterministic Archetype Mapping**: Centroid feature profiles are normalized using z-scores to guarantee 100% deterministic labeling across re-runs.

---

## 📸 Screenshots Placeholder

> *Note: Place screenshots of the user interface below.*

### 1. Main Dashboard & Team Management
![Main Dashboard](docs/screenshots/dashboard.png)
*Figure 1: Main Dashboard displaying team overview, quick action tiles, and light/dark theme toggle.*

---

### 2. Live Win Probability Predictor
![Win Probability Predictor](docs/screenshots/win_predictor.png)
*Figure 2: Real-time 2nd-innings win probability calculation powered by XGBoost.*

---

### 3. Player Form & Analytics Visualizer
![Player Form Predictor](docs/screenshots/player_form.png)
*Figure 3: Player rolling 5-match performance chart, composite form rating, and trend indicators.*

---

### 4. Player Archetype Clustering Visualization
![Player Clusters](docs/screenshots/clusters.png)
*Figure 4: K-Means player clustering distribution showing 5 cricket archetypes.*

---

### 5. Head-to-Head & Venue Breakdown
![Head-to-Head Comparison](docs/screenshots/h2h_comparison.png)
*Figure 5: Historical head-to-head match stats and venue performance analysis.*

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is open-source under the [ISC License](LICENSE).

---

## 👥 Authors

- **Chandan**
- **Srihari**
- **Gagan**

---

*© 2026 Cricket Companion & Analytics Engine. Built with Node.js, Python, FastAPI & XGBoost.*
