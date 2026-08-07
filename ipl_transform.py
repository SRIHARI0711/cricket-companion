"""
IPL Dataset Cleaner & Feature Engineer — Phase 2: Analytics Layer
=================================================================
Reads the raw Kaggle IPL CSVs (matches.csv + deliveries.csv), performs:

  1. Missing-value handling
  2. Team-name standardisation
  3. Date-format conversion
  4. Feature engineering
       • strike_rate          (batting)
       • economy_rate         (bowling)
       • batting_average      (batting)
       • bowling_average      (bowling)
       • boundary_percentage  (batting)

Outputs two new MySQL tables:
  • ipl_batting_stats   — one row per player per season
  • ipl_bowling_stats   — one row per player per season

Usage:
    python ipl_transform.py
"""

import os
import sys
import logging
import getpass
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# ── Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError) ─────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cricket_companion"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}

RAW_DIR       = Path("ipl_data_raw")
MATCHES_CSV   = RAW_DIR / "matches.csv"
DELIVERIES_CSV = RAW_DIR / "deliveries.csv"

# ── Team-name aliases ─────────────────────────────────────────────────────────
# Maps every historical franchise variant → canonical current name
TEAM_ALIASES: dict[str, str] = {
    # Delhi
    "Delhi Daredevils":                 "Delhi Capitals",
    # Hyderabad
    "Deccan Chargers":                  "Sunrisers Hyderabad",
    # Pune
    "Pune Warriors":                    "Rising Pune Supergiant",
    "Rising Pune Supergiants":          "Rising Pune Supergiant",
    # Punjab
    "Kings XI Punjab":                  "Punjab Kings",
    # Bangalore
    "Royal Challengers Bangalore":      "Royal Challengers Bengaluru",
    # Kochi (defunct – keep as-is but normalise spelling)
    "Kochi Tuskers Kerala":             "Kochi Tuskers Kerala",
    # Gujarat (two stints)
    "Gujarat Lions":                    "Gujarat Lions",
    "Gujarat Titans":                   "Gujarat Titans",
}


def normalize_team(name: str) -> str:
    """Return the canonical team name; fall back to the original if unknown."""
    if not isinstance(name, str) or name.strip() in ("", "nan", "None"):
        return "Unknown"
    cleaned = name.strip()
    return TEAM_ALIASES.get(cleaned, cleaned)


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_connection():
    cfg = DB_CONFIG.copy()
    if not cfg["password"]:
        cfg["password"] = getpass.getpass("MySQL password for root@localhost: ")
    conn = mysql.connector.connect(**cfg)
    conn.autocommit = False
    return conn


def drop_and_create_tables(cursor) -> None:
    """
    Create (or recreate) the two analytics tables.
    We DROP first so repeated runs are idempotent.
    """

    cursor.execute("DROP TABLE IF EXISTS ipl_batting_stats")
    cursor.execute("DROP TABLE IF EXISTS ipl_bowling_stats")

    cursor.execute("""
        CREATE TABLE ipl_batting_stats (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            player_name         VARCHAR(120)  NOT NULL,
            season              VARCHAR(10)   NOT NULL,
            team                VARCHAR(100),
            innings             INT           DEFAULT 0 COMMENT 'Innings batted',
            runs_scored         INT           DEFAULT 0,
            balls_faced         INT           DEFAULT 0,
            dismissals          INT           DEFAULT 0 COMMENT 'Times out',
            fours               INT           DEFAULT 0,
            sixes               INT           DEFAULT 0,
            strike_rate         DECIMAL(7,2)  COMMENT '(runs/balls)*100',
            batting_average     DECIMAL(7,2)  COMMENT 'runs / dismissals; NULL if never out',
            boundary_percentage DECIMAL(6,2)  COMMENT '% balls that went to boundary',
            highest_score       INT           DEFAULT 0,
            fifties             INT           DEFAULT 0 COMMENT 'Scores 50-99',
            hundreds            INT           DEFAULT 0 COMMENT 'Scores 100+',
            created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_batting_player (player_name),
            INDEX idx_batting_season (season),
            UNIQUE KEY uq_batting (player_name, season, team)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE ipl_bowling_stats (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            player_name       VARCHAR(120)  NOT NULL,
            season            VARCHAR(10)   NOT NULL,
            team              VARCHAR(100),
            innings_bowled    INT           DEFAULT 0,
            overs_bowled      DECIMAL(6,1)  DEFAULT 0.0,
            balls_bowled      INT           DEFAULT 0,
            runs_conceded     INT           DEFAULT 0,
            wickets           INT           DEFAULT 0,
            economy_rate      DECIMAL(6,2)  COMMENT 'runs / overs',
            bowling_average   DECIMAL(7,2)  COMMENT 'runs_conceded / wickets; NULL if 0 wickets',
            bowling_sr        DECIMAL(7,2)  COMMENT 'balls / wickets; NULL if 0 wickets',
            best_bowling      VARCHAR(10)   COMMENT 'e.g. 5/17',
            four_wicket_hauls INT           DEFAULT 0,
            five_wicket_hauls INT           DEFAULT 0,
            created_at        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_bowling_player (player_name),
            INDEX idx_bowling_season (season),
            UNIQUE KEY uq_bowling (player_name, season, team)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    log.info("Tables ipl_batting_stats and ipl_bowling_stats created.")


# ── Step 1: Load raw CSVs ─────────────────────────────────────────────────────

def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    log.info(f"Reading {MATCHES_CSV} …")
    matches = pd.read_csv(MATCHES_CSV, low_memory=False)
    log.info(f"  → {len(matches):,} match rows, {matches.shape[1]} columns")

    log.info(f"Reading {DELIVERIES_CSV} …")
    deliveries = pd.read_csv(DELIVERIES_CSV, low_memory=False)
    log.info(f"  → {len(deliveries):,} delivery rows, {deliveries.shape[1]} columns")

    return matches, deliveries


# ── Step 2: Clean matches ─────────────────────────────────────────────────────

def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning matches …")

    # --- Date format conversion ---
    # The Kaggle dataset uses ISO dates (YYYY-MM-DD).  Convert to proper dtype.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    null_dates = df["date"].isna().sum()
    if null_dates:
        log.warning(f"  {null_dates} match rows have unparseable dates; set to NaT.")

    # --- Season normalisation ---
    # Some rows have "2007/08", others have plain "2020". Normalise to end-year.
    def parse_season(s):
        s = str(s).strip()
        if "/" in s:
            return s.split("/")[0]  # "2007/08" → "2007"
        return s
    df["season"] = df["season"].apply(parse_season)

    # --- Team-name standardisation ---
    for col in ("team1", "team2", "toss_winner", "winner"):
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: normalize_team(v) if pd.notna(v) else "Unknown"
            )

    # --- Missing-value handling ---
    df["city"]            = df["city"].fillna("Unknown")
    df["venue"]           = df["venue"].fillna("Unknown")
    df["player_of_match"] = df["player_of_match"].fillna("Unknown")
    df["umpire1"]         = df["umpire1"].fillna("Unknown")
    df["umpire2"]         = df["umpire2"].fillna("Unknown")
    df["method"]          = df["method"].fillna("N/A")
    df["super_over"]      = df["super_over"].fillna("N")
    df["winner"]          = df["winner"].where(df["winner"].notna(), "No Result")
    df["result_margin"]   = pd.to_numeric(df["result_margin"], errors="coerce").fillna(0)
    df["target_runs"]     = pd.to_numeric(df["target_runs"],   errors="coerce").fillna(0)
    df["target_overs"]    = pd.to_numeric(df["target_overs"],  errors="coerce").fillna(20)

    log.info(f"  Matches cleaned: {len(df):,} rows")
    log.info(f"  Seasons present: {sorted(df['season'].unique())}")
    return df


# ── Step 3: Clean deliveries ─────────────────────────────────────────────────

def clean_deliveries(df: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning deliveries …")

    # --- Column aliasing for cross-version compatibility ---
    df = df.rename(columns={
        "batsman":      "batter",
        "batsman_runs": "batsman_runs",
        "runs_off_bat": "batsman_runs",
    })

    # --- Numeric coercions ---
    for col in ("batsman_runs", "extra_runs", "total_runs", "is_wicket", "over", "ball"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # --- Fill sparse string columns ---
    df["extras_type"]       = df["extras_type"].fillna("none")
    df["player_dismissed"]  = df["player_dismissed"].fillna("")
    df["dismissal_kind"]    = df["dismissal_kind"].fillna("")
    df["fielder"]           = df["fielder"].fillna("")

    # --- Team name standardisation ---
    for col in ("batting_team", "bowling_team"):
        if col in df.columns:
            df[col] = df[col].apply(normalize_team)

    # --- Attach season from matches ---
    season_map = matches.set_index("id")["season"].to_dict()
    df["season"] = df["match_id"].map(season_map).fillna("Unknown")

    # --- Derive "is_legal_ball" (wide or no-ball = not a legal delivery for SR/economy) ---
    df["is_wide"]   = (df["extras_type"] == "wides").astype(int)
    df["is_noball"] = (df["extras_type"] == "noballs").astype(int)
    df["is_legal"]  = ((df["is_wide"] == 0) & (df["is_noball"] == 0)).astype(int)

    # --- Boundary flags ---
    df["is_four"] = ((df["batsman_runs"] == 4) & (df["is_wide"] == 0)).astype(int)
    df["is_six"]  = ((df["batsman_runs"] == 6) & (df["is_wide"] == 0)).astype(int)

    # --- Wicket flag — exclude run-outs (bowler not credited) ---
    df["is_bowler_wicket"] = (
        (df["is_wicket"] == 1) &
        (df["dismissal_kind"] != "run out")
    ).astype(int)

    log.info(f"  Deliveries cleaned: {len(df):,} rows")
    return df


# ── Step 4: Engineer batting stats ───────────────────────────────────────────

def build_batting_stats(deliveries: pd.DataFrame) -> pd.DataFrame:
    log.info("Engineering batting stats …")

    # Only count legal balls faced by batter for SR (exclude wides)
    legal = deliveries[deliveries["is_wide"] == 0].copy()

    # ── Per-match innings scores (to compute highest score, 50s, 100s) ──
    match_bat = (
        legal.groupby(["match_id", "season", "batter", "batting_team"])
        .agg(
            runs       = ("batsman_runs", "sum"),
            balls      = ("batsman_runs", "count"),
            fours      = ("is_four", "sum"),
            sixes      = ("is_six", "sum"),
            dismissed  = ("is_wicket", "max"),   # 1 if dismissed at least once
        )
        .reset_index()
    )

    # ── Aggregate to season level ──
    season_bat = (
        match_bat.groupby(["batter", "season", "batting_team"])
        .agg(
            innings       = ("match_id", "nunique"),
            runs_scored   = ("runs", "sum"),
            balls_faced   = ("balls", "sum"),
            dismissals    = ("dismissed", "sum"),
            fours         = ("fours", "sum"),
            sixes         = ("sixes", "sum"),
            highest_score = ("runs", "max"),
            fifties       = ("runs", lambda x: ((x >= 50) & (x < 100)).sum()),
            hundreds      = ("runs", lambda x: (x >= 100).sum()),
        )
        .reset_index()
    )

    # ── Computed features ──

    # Strike Rate = (runs_scored / balls_faced) * 100
    season_bat["strike_rate"] = np.where(
        season_bat["balls_faced"] > 0,
        (season_bat["runs_scored"] / season_bat["balls_faced"] * 100).round(2),
        np.nan,
    )

    # Batting Average = runs_scored / dismissals (None if never dismissed)
    season_bat["batting_average"] = np.where(
        season_bat["dismissals"] > 0,
        (season_bat["runs_scored"] / season_bat["dismissals"]).round(2),
        np.nan,
    )

    # Boundary Percentage = (4s + 6s) / balls_faced * 100
    season_bat["boundary_percentage"] = np.where(
        season_bat["balls_faced"] > 0,
        ((season_bat["fours"] + season_bat["sixes"]) / season_bat["balls_faced"] * 100).round(2),
        np.nan,
    )

    # Clean up types
    season_bat = season_bat.rename(columns={
        "batter":       "player_name",
        "batting_team": "team",
    })

    int_cols = ["innings", "runs_scored", "balls_faced", "dismissals",
                "fours", "sixes", "highest_score", "fifties", "hundreds"]
    season_bat[int_cols] = season_bat[int_cols].fillna(0).astype(int)

    log.info(f"  Batting stat rows: {len(season_bat):,}")
    log.info(f"  Sample SR range  : {season_bat['strike_rate'].min():.1f} – {season_bat['strike_rate'].max():.1f}")
    return season_bat


# ── Step 5: Engineer bowling stats ───────────────────────────────────────────

def build_bowling_stats(deliveries: pd.DataFrame) -> pd.DataFrame:
    log.info("Engineering bowling stats …")

    # For economy & bowling SR, only legal balls count
    # For runs_conceded, count all balls (including wides/no-balls)
    match_bowl_runs = (
        deliveries.groupby(["match_id", "season", "bowler", "bowling_team"])
        .agg(
            runs_conceded = ("total_runs", "sum"),
            balls_legal   = ("is_legal", "sum"),
            wickets       = ("is_bowler_wicket", "sum"),
        )
        .reset_index()
    )

    # ── Aggregate to season level ──
    season_bowl = (
        match_bowl_runs.groupby(["bowler", "season", "bowling_team"])
        .agg(
            innings_bowled = ("match_id", "nunique"),
            balls_bowled   = ("balls_legal", "sum"),
            runs_conceded  = ("runs_conceded", "sum"),
            wickets        = ("wickets", "sum"),
        )
        .reset_index()
    )

    # Overs = whole overs + (remaining balls / 10)  — cricket notation
    season_bowl["overs_bowled"] = (
        season_bowl["balls_bowled"] // 6 + (season_bowl["balls_bowled"] % 6) / 10
    ).round(1)

    # ── Computed features ──

    # Economy Rate = runs_conceded / overs_bowled
    season_bowl["economy_rate"] = np.where(
        season_bowl["balls_bowled"] > 0,
        (season_bowl["runs_conceded"] / (season_bowl["balls_bowled"] / 6)).round(2),
        np.nan,
    )

    # Bowling Average = runs_conceded / wickets (NaN if 0 wickets)
    season_bowl["bowling_average"] = np.where(
        season_bowl["wickets"] > 0,
        (season_bowl["runs_conceded"] / season_bowl["wickets"]).round(2),
        np.nan,
    )

    # Bowling Strike Rate = balls_bowled / wickets (NaN if 0 wickets)
    season_bowl["bowling_sr"] = np.where(
        season_bowl["wickets"] > 0,
        (season_bowl["balls_bowled"] / season_bowl["wickets"]).round(2),
        np.nan,
    )

    # ── Best bowling (most wickets in a single match; ties broken by fewest runs) ──
    match_bowl_runs["sort_key"] = (
        match_bowl_runs["wickets"] * 10000 - match_bowl_runs["runs_conceded"]
    )
    best = (
        match_bowl_runs.sort_values("sort_key", ascending=False)
        .groupby(["bowler", "season", "bowling_team"])
        .first()
        .reset_index()[["bowler", "season", "bowling_team", "wickets", "runs_conceded"]]
    )
    best["best_bowling"] = (
        best["wickets"].astype(str) + "/" + best["runs_conceded"].astype(str)
    )
    best = best.rename(columns={
        "bowler":       "bowler_name",
        "bowling_team": "team_best",
    })

    season_bowl = season_bowl.rename(columns={
        "bowler":       "player_name",
        "bowling_team": "team",
    })

    season_bowl = season_bowl.merge(
        best[["bowler_name", "season", "team_best", "best_bowling"]],
        left_on  = ["player_name", "season", "team"],
        right_on = ["bowler_name", "season", "team_best"],
        how="left",
    ).drop(columns=["bowler_name", "team_best"], errors="ignore")

    # ── Hauls ──
    hauls = (
        match_bowl_runs.groupby(["bowler", "season", "bowling_team"])
        .apply(
            lambda g: pd.Series({
                "four_wicket_hauls": (g["wickets"] == 4).sum(),
                "five_wicket_hauls": (g["wickets"] >= 5).sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    hauls = hauls.rename(columns={"bowler": "player_name", "bowling_team": "team"})

    season_bowl = season_bowl.merge(hauls, on=["player_name", "season", "team"], how="left")

    # Final type cleanup
    int_cols = ["innings_bowled", "balls_bowled", "runs_conceded", "wickets",
                "four_wicket_hauls", "five_wicket_hauls"]
    season_bowl[int_cols] = season_bowl[int_cols].fillna(0).astype(int)
    season_bowl["best_bowling"] = season_bowl["best_bowling"].fillna("0/0")

    log.info(f"  Bowling stat rows: {len(season_bowl):,}")
    log.info(f"  Eco rate range   : {season_bowl['economy_rate'].min():.2f} – {season_bowl['economy_rate'].max():.2f}")
    return season_bowl


# ── Step 6: Save to MySQL ─────────────────────────────────────────────────────

def _to_python(val):
    """Convert numpy/pandas scalars to native Python types for mysql-connector."""
    if pd.isna(val) if not isinstance(val, (list, dict, pd.DataFrame)) else False:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    return val


def insert_batting(cursor, df: pd.DataFrame) -> int:
    sql = """
        INSERT INTO ipl_batting_stats
            (player_name, season, team, innings, runs_scored, balls_faced,
             dismissals, fours, sixes, strike_rate, batting_average,
             boundary_percentage, highest_score, fifties, hundreds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            innings             = VALUES(innings),
            runs_scored         = VALUES(runs_scored),
            balls_faced         = VALUES(balls_faced),
            dismissals          = VALUES(dismissals),
            fours               = VALUES(fours),
            sixes               = VALUES(sixes),
            strike_rate         = VALUES(strike_rate),
            batting_average     = VALUES(batting_average),
            boundary_percentage = VALUES(boundary_percentage),
            highest_score       = VALUES(highest_score),
            fifties             = VALUES(fifties),
            hundreds            = VALUES(hundreds)
    """
    cols = [
        "player_name", "season", "team", "innings", "runs_scored", "balls_faced",
        "dismissals", "fours", "sixes", "strike_rate", "batting_average",
        "boundary_percentage", "highest_score", "fifties", "hundreds",
    ]
    rows = [
        tuple(_to_python(row[c]) for c in cols)
        for _, row in df.iterrows()
    ]
    cursor.executemany(sql, rows)
    log.info(f"  ✓ ipl_batting_stats: {cursor.rowcount} rows upserted")
    return cursor.rowcount


def insert_bowling(cursor, df: pd.DataFrame) -> int:
    sql = """
        INSERT INTO ipl_bowling_stats
            (player_name, season, team, innings_bowled, overs_bowled, balls_bowled,
             runs_conceded, wickets, economy_rate, bowling_average, bowling_sr,
             best_bowling, four_wicket_hauls, five_wicket_hauls)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            innings_bowled    = VALUES(innings_bowled),
            overs_bowled      = VALUES(overs_bowled),
            balls_bowled      = VALUES(balls_bowled),
            runs_conceded     = VALUES(runs_conceded),
            wickets           = VALUES(wickets),
            economy_rate      = VALUES(economy_rate),
            bowling_average   = VALUES(bowling_average),
            bowling_sr        = VALUES(bowling_sr),
            best_bowling      = VALUES(best_bowling),
            four_wicket_hauls = VALUES(four_wicket_hauls),
            five_wicket_hauls = VALUES(five_wicket_hauls)
    """
    cols = [
        "player_name", "season", "team", "innings_bowled", "overs_bowled", "balls_bowled",
        "runs_conceded", "wickets", "economy_rate", "bowling_average", "bowling_sr",
        "best_bowling", "four_wicket_hauls", "five_wicket_hauls",
    ]
    rows = [
        tuple(_to_python(row[c]) for c in cols)
        for _, row in df.iterrows()
    ]
    cursor.executemany(sql, rows)
    log.info(f"  ✓ ipl_bowling_stats: {cursor.rowcount} rows upserted")
    return cursor.rowcount


# ── Step 7: Validation summary ────────────────────────────────────────────────

def print_validation_summary(batting: pd.DataFrame, bowling: pd.DataFrame) -> None:
    sep = "─" * 60
    log.info(f"\n{sep}")
    log.info("DATA VALIDATION SUMMARY")
    log.info(sep)

    log.info("\n▶ BATTING STATS")
    log.info(f"  Total rows        : {len(batting):,}")
    log.info(f"  Unique players    : {batting['player_name'].nunique():,}")
    log.info(f"  Seasons covered   : {sorted(batting['season'].unique())}")
    log.info(f"  Null strike_rate  : {batting['strike_rate'].isna().sum():,}")
    log.info(f"  Null bat_average  : {batting['batting_average'].isna().sum():,}  (never-dismissed batters)")
    log.info(f"  Null bound_pct    : {batting['boundary_percentage'].isna().sum():,}")
    log.info(f"  Top 5 by total runs:\n{batting.nlargest(5, 'runs_scored')[['player_name','season','team','runs_scored','strike_rate','batting_average']].to_string(index=False)}")

    log.info("\n▶ BOWLING STATS")
    log.info(f"  Total rows        : {len(bowling):,}")
    log.info(f"  Unique bowlers    : {bowling['player_name'].nunique():,}")
    log.info(f"  Null economy_rate : {bowling['economy_rate'].isna().sum():,}")
    log.info(f"  Null bowl_average : {bowling['bowling_average'].isna().sum():,}  (0-wicket seasons)")
    log.info(f"  Top 5 by wickets:\n{bowling.nlargest(5, 'wickets')[['player_name','season','team','wickets','economy_rate','bowling_average']].to_string(index=False)}")

    log.info(sep)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("═" * 60)
    log.info("IPL Transform — Phase 2: Analytics Layer")
    log.info("═" * 60)

    # 1. Verify raw files exist
    for f in (MATCHES_CSV, DELIVERIES_CSV):
        if not f.exists():
            log.error(f"Required file not found: {f}")
            log.error("Run load_ipl_data.py first to download the Kaggle dataset.")
            sys.exit(1)

    # 2. Load
    matches_raw, deliveries_raw = load_raw()

    # 3. Clean
    matches_clean    = clean_matches(matches_raw)
    deliveries_clean = clean_deliveries(deliveries_raw, matches_clean)

    # 4. Engineer features
    batting_stats = build_batting_stats(deliveries_clean)
    bowling_stats = build_bowling_stats(deliveries_clean)

    # 5. In-memory validation
    print_validation_summary(batting_stats, bowling_stats)

    # 6. Connect to DB
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        log.info(f"\nConnected to MySQL: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    except Error as exc:
        log.error(f"DB connection failed: {exc}")
        sys.exit(1)

    # 7. Create tables + insert
    try:
        log.info("\n── Creating analytics tables ─────────────────────────")
        drop_and_create_tables(cursor)

        log.info("\n── Inserting batting stats ───────────────────────────")
        insert_batting(cursor, batting_stats)

        log.info("\n── Inserting bowling stats ───────────────────────────")
        insert_bowling(cursor, bowling_stats)

        conn.commit()
        log.info("\n✅ All analytics data committed successfully.")

    except Exception as exc:
        conn.rollback()
        log.error(f"Error during insert — rolled back: {exc}")
        raise
    finally:
        cursor.close()
        conn.close()

    # 8. Final row-count check
    log.info("\n── Final row counts ──────────────────────────────────")
    try:
        conn2  = get_connection()
        cur2   = conn2.cursor()
        for tbl in ("ipl_batting_stats", "ipl_bowling_stats"):
            cur2.execute(f"SELECT COUNT(*) FROM {tbl}")
            (n,) = cur2.fetchone()
            log.info(f"  {tbl:<24}: {n:>7,} rows")
        cur2.close()
        conn2.close()
    except Exception:
        pass

    log.info("\nDone! Run your analytics queries against ipl_batting_stats & ipl_bowling_stats.")


if __name__ == "__main__":
    main()
