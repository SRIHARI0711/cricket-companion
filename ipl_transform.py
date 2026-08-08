"""
IPL Dataset Cleaner & Feature Engineer — Phase 1 #3: Analytics Layer
=====================================================================
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

# ── Force UTF-8 output on Windows ─────────────────────────────────────────────
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

RAW_DIR        = Path("ipl_data_raw")
MATCHES_CSV    = RAW_DIR / "matches.csv"
DELIVERIES_CSV = RAW_DIR / "deliveries.csv"

# ── Team-name aliases ─────────────────────────────────────────────────────────
TEAM_ALIASES: dict[str, str] = {
    "Delhi Daredevils":            "Delhi Capitals",
    "Deccan Chargers":             "Sunrisers Hyderabad",
    "Pune Warriors":               "Rising Pune Supergiant",
    "Rising Pune Supergiants":     "Rising Pune Supergiant",
    "Kings XI Punjab":             "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Kochi Tuskers Kerala":        "Kochi Tuskers Kerala",
    "Gujarat Lions":               "Gujarat Lions",
    "Gujarat Titans":              "Gujarat Titans",
}


def normalize_team(name: str) -> str:
    if not isinstance(name, str) or name.strip() in ("", "nan", "None"):
        return "Unknown"
    return TEAM_ALIASES.get(name.strip(), name.strip())


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_connection():
    cfg = DB_CONFIG.copy()
    if not cfg["password"]:
        cfg["password"] = getpass.getpass("MySQL password for root@localhost: ")
    conn = mysql.connector.connect(**cfg)
    conn.autocommit = False
    return conn


def drop_and_create_tables(cursor) -> None:
    """Recreate analytics tables — idempotent on repeated runs."""
    cursor.execute("DROP TABLE IF EXISTS ipl_batting_stats")
    cursor.execute("DROP TABLE IF EXISTS ipl_bowling_stats")

    cursor.execute("""
        CREATE TABLE ipl_batting_stats (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            player_name         VARCHAR(120)  NOT NULL,
            season              VARCHAR(10)   NOT NULL,
            team                VARCHAR(100),
            innings             INT           DEFAULT 0,
            runs_scored         INT           DEFAULT 0,
            balls_faced         INT           DEFAULT 0,
            dismissals          INT           DEFAULT 0,
            fours               INT           DEFAULT 0,
            sixes               INT           DEFAULT 0,
            strike_rate         DECIMAL(7,2),
            batting_average     DECIMAL(7,2),
            boundary_percentage DECIMAL(6,2),
            highest_score       INT           DEFAULT 0,
            fifties             INT           DEFAULT 0,
            hundreds            INT           DEFAULT 0,
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
            economy_rate      DECIMAL(6,2),
            bowling_average   DECIMAL(7,2),
            bowling_sr        DECIMAL(7,2),
            best_bowling      VARCHAR(10),
            four_wicket_hauls INT           DEFAULT 0,
            five_wicket_hauls INT           DEFAULT 0,
            created_at        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_bowling_player (player_name),
            INDEX idx_bowling_season (season),
            UNIQUE KEY uq_bowling (player_name, season, team)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    log.info("Tables ipl_batting_stats and ipl_bowling_stats (re)created.")


# ── Step 1: Load raw CSVs ─────────────────────────────────────────────────────

def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    for f in (MATCHES_CSV, DELIVERIES_CSV):
        if not f.exists():
            log.error(f"Required file not found: {f}")
            log.error("Run load_ipl_data.py first to download the Kaggle dataset.")
            sys.exit(1)

    log.info(f"Reading {MATCHES_CSV} …")
    matches = pd.read_csv(MATCHES_CSV, low_memory=False)
    log.info(f"  → {len(matches):,} rows, {matches.shape[1]} columns")
    log.info(f"  Columns: {list(matches.columns)}")

    log.info(f"Reading {DELIVERIES_CSV} …")
    deliveries = pd.read_csv(DELIVERIES_CSV, low_memory=False)
    log.info(f"  → {len(deliveries):,} rows, {deliveries.shape[1]} columns")
    log.info(f"  Columns: {list(deliveries.columns)}")

    return matches, deliveries


# ── Step 2: Clean matches ─────────────────────────────────────────────────────

def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning matches …")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    null_dates = df["date"].isna().sum()
    if null_dates:
        log.warning(f"  {null_dates} rows have unparseable dates.")

    def parse_season(s):
        s = str(s).strip()
        return s.split("/")[0] if "/" in s else s

    df["season"] = df["season"].apply(parse_season)

    for col in ("team1", "team2", "toss_winner", "winner"):
        if col in df.columns:
            df[col] = df[col].apply(lambda v: normalize_team(v) if pd.notna(v) else "Unknown")

    fill_unknown = ["city", "venue", "player_of_match", "umpire1", "umpire2"]
    for col in fill_unknown:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    if "method" in df.columns:
        df["method"] = df["method"].fillna("N/A")
    if "super_over" in df.columns:
        df["super_over"] = df["super_over"].fillna("N")
    if "winner" in df.columns:
        df["winner"] = df["winner"].where(df["winner"].notna(), "No Result")
    if "result_margin" in df.columns:
        df["result_margin"] = pd.to_numeric(df["result_margin"], errors="coerce").fillna(0)
    if "target_runs" in df.columns:
        df["target_runs"] = pd.to_numeric(df["target_runs"], errors="coerce").fillna(0)
    if "target_overs" in df.columns:
        df["target_overs"] = pd.to_numeric(df["target_overs"], errors="coerce").fillna(20)

    log.info(f"  Matches cleaned: {len(df):,} rows")
    log.info(f"  Seasons found  : {sorted(df['season'].unique())}")
    return df


# ── Step 3: Clean deliveries ─────────────────────────────────────────────────

def clean_deliveries(df: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning deliveries …")

    # ── Normalise column names across dataset versions ──
    rename_map = {}
    if "batsman" in df.columns and "batter" not in df.columns:
        rename_map["batsman"] = "batter"
    if "runs_off_bat" in df.columns and "batsman_runs" not in df.columns:
        rename_map["runs_off_bat"] = "batsman_runs"
    if rename_map:
        df = df.rename(columns=rename_map)
        log.info(f"  Renamed columns: {rename_map}")

    # ── Numeric coercions ──
    for col in ("batsman_runs", "extra_runs", "total_runs", "is_wicket", "over", "ball"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ── Fill string columns ──
    for col in ("extras_type", "player_dismissed", "dismissal_kind", "fielder"):
        if col in df.columns:
            df[col] = df[col].fillna("")

    # ── Team names ──
    for col in ("batting_team", "bowling_team"):
        if col in df.columns:
            df[col] = df[col].apply(normalize_team)

    # ── Attach season ──
    # The match-id column may be called "match_id" or "id"
    mid_col = "match_id" if "match_id" in df.columns else "id"
    season_map = matches.set_index("id")["season"].to_dict() if "id" in matches.columns else {}
    df["season"] = df[mid_col].map(season_map).fillna("Unknown")

    # ── Derived flags ──
    df["is_wide"]   = (df.get("extras_type", pd.Series(dtype=str)) == "wides").astype(int)
    df["is_noball"] = (df.get("extras_type", pd.Series(dtype=str)) == "noballs").astype(int)
    df["is_legal"]  = ((df["is_wide"] == 0) & (df["is_noball"] == 0)).astype(int)
    df["is_four"]   = ((df.get("batsman_runs", 0) == 4) & (df["is_wide"] == 0)).astype(int)
    df["is_six"]    = ((df.get("batsman_runs", 0) == 6) & (df["is_wide"] == 0)).astype(int)

    # ── Wicket flag — exclude run-outs ──
    if "is_wicket" in df.columns:
        df["is_bowler_wicket"] = (
            (df["is_wicket"] == 1) &
            (df.get("dismissal_kind", "") != "run out")
        ).astype(int)
    elif "player_dismissed" in df.columns:
        df["is_bowler_wicket"] = (
            (df["player_dismissed"] != "") &
            (df.get("dismissal_kind", "") != "run out")
        ).astype(int)
    else:
        df["is_bowler_wicket"] = 0

    log.info(f"  Deliveries cleaned: {len(df):,} rows")
    return df


# ── Step 4: Engineer batting stats ───────────────────────────────────────────

def build_batting_stats(deliveries: pd.DataFrame) -> pd.DataFrame:
    log.info("Engineering batting stats …")

    bat_col  = "batter" if "batter" in deliveries.columns else "batsman"
    runs_col = "batsman_runs" if "batsman_runs" in deliveries.columns else "runs_off_bat"
    mid_col  = "match_id" if "match_id" in deliveries.columns else "id"

    # Exclude wides for balls-faced count
    legal = deliveries[deliveries["is_wide"] == 0].copy()

    # Batting team column (may not exist in all dataset versions)
    team_col = "batting_team" if "batting_team" in deliveries.columns else None

    group_cols = [mid_col, "season", bat_col]
    if team_col:
        group_cols.append(team_col)

    # ── Per-match batting ──
    match_bat = (
        legal.groupby(group_cols)
        .agg(
            runs      = (runs_col, "sum"),
            balls     = (runs_col, "count"),
            fours     = ("is_four", "sum"),
            sixes     = ("is_six", "sum"),
            dismissed = ("is_wicket" if "is_wicket" in legal.columns else "is_bowler_wicket", "max"),
        )
        .reset_index()
    )

    # ── Season aggregation ──
    agg_group = ["season", bat_col]
    if team_col:
        agg_group.append(team_col)

    season_bat = (
        match_bat.groupby(agg_group)
        .agg(
            innings       = (mid_col, "nunique"),
            runs_scored   = ("runs", "sum"),
            balls_faced   = ("balls", "sum"),
            dismissals    = ("dismissed", "sum"),
            fours         = ("fours", "sum"),
            sixes         = ("sixes", "sum"),
            highest_score = ("runs", "max"),
        )
        .reset_index()
    )

    # ── Fifties and hundreds — computed separately to avoid lambda in agg ──
    # (pandas 2.2 deprecates named aggregation lambdas in some contexts)
    match_runs = match_bat.groupby(agg_group + [mid_col])["runs"].sum().reset_index()
    hauls = (
        match_runs.groupby(agg_group)
        .agg(
            fifties  = ("runs", lambda x: ((x >= 50) & (x < 100)).sum()),
            hundreds = ("runs", lambda x: (x >= 100).sum()),
        )
        .reset_index()
    )
    season_bat = season_bat.merge(hauls, on=agg_group, how="left")

    # ── Computed features ──
    season_bat["strike_rate"] = np.where(
        season_bat["balls_faced"] > 0,
        (season_bat["runs_scored"] / season_bat["balls_faced"] * 100).round(2),
        np.nan,
    )
    season_bat["batting_average"] = np.where(
        season_bat["dismissals"] > 0,
        (season_bat["runs_scored"] / season_bat["dismissals"]).round(2),
        np.nan,
    )
    season_bat["boundary_percentage"] = np.where(
        season_bat["balls_faced"] > 0,
        ((season_bat["fours"] + season_bat["sixes"]) / season_bat["balls_faced"] * 100).round(2),
        np.nan,
    )

    # ── Rename to canonical schema columns ──
    rename = {bat_col: "player_name"}
    if team_col:
        rename[team_col] = "team"
    season_bat = season_bat.rename(columns=rename)
    if "team" not in season_bat.columns:
        season_bat["team"] = "Unknown"

    int_cols = ["innings", "runs_scored", "balls_faced", "dismissals",
                "fours", "sixes", "highest_score", "fifties", "hundreds"]
    season_bat[int_cols] = season_bat[int_cols].fillna(0).astype(int)

    log.info(f"  Batting stat rows: {len(season_bat):,}")
    log.info(f"  SR range         : {season_bat['strike_rate'].min():.1f}–{season_bat['strike_rate'].max():.1f}")
    return season_bat


# ── Step 5: Engineer bowling stats ───────────────────────────────────────────

def build_bowling_stats(deliveries: pd.DataFrame) -> pd.DataFrame:
    log.info("Engineering bowling stats …")

    mid_col  = "match_id" if "match_id" in deliveries.columns else "id"
    team_col = "bowling_team" if "bowling_team" in deliveries.columns else None

    group_cols = [mid_col, "season", "bowler"]
    if team_col:
        group_cols.append(team_col)

    # ── Per-match bowling ──
    match_bowl = (
        deliveries.groupby(group_cols)
        .agg(
            runs_conceded = ("total_runs", "sum"),
            balls_legal   = ("is_legal", "sum"),
            wickets       = ("is_bowler_wicket", "sum"),
        )
        .reset_index()
    )

    # ── Season aggregation ──
    agg_group = ["season", "bowler"]
    if team_col:
        agg_group.append(team_col)

    season_bowl = (
        match_bowl.groupby(agg_group)
        .agg(
            innings_bowled = (mid_col, "nunique"),
            balls_bowled   = ("balls_legal", "sum"),
            runs_conceded  = ("runs_conceded", "sum"),
            wickets        = ("wickets", "sum"),
        )
        .reset_index()
    )

    season_bowl["overs_bowled"] = (
        season_bowl["balls_bowled"] // 6 + (season_bowl["balls_bowled"] % 6) / 10
    ).round(1)

    season_bowl["economy_rate"] = np.where(
        season_bowl["balls_bowled"] > 0,
        (season_bowl["runs_conceded"] / (season_bowl["balls_bowled"] / 6)).round(2),
        np.nan,
    )
    season_bowl["bowling_average"] = np.where(
        season_bowl["wickets"] > 0,
        (season_bowl["runs_conceded"] / season_bowl["wickets"]).round(2),
        np.nan,
    )
    season_bowl["bowling_sr"] = np.where(
        season_bowl["wickets"] > 0,
        (season_bowl["balls_bowled"] / season_bowl["wickets"]).round(2),
        np.nan,
    )

    # ── Best bowling per player-season (fix: no include_groups) ──
    # Sort so the best inning is first, then take first row per group
    match_bowl["sort_key"] = match_bowl["wickets"] * 10000 - match_bowl["runs_conceded"]
    best = (
        match_bowl
        .sort_values("sort_key", ascending=False)
        .groupby(agg_group, as_index=False)   # ← no include_groups needed here
        .first()
        [agg_group + ["wickets", "runs_conceded"]]
    )
    best["best_bowling"] = best["wickets"].astype(str) + "/" + best["runs_conceded"].astype(str)
    best = best[agg_group + ["best_bowling"]]

    season_bowl = season_bowl.merge(best, on=agg_group, how="left")
    season_bowl["best_bowling"] = season_bowl["best_bowling"].fillna("0/0")

    # ── 4-wicket and 5-wicket hauls (fix: avoid deprecated apply pattern) ──
    match_bowl["is_4w"] = (match_bowl["wickets"] == 4).astype(int)
    match_bowl["is_5w"] = (match_bowl["wickets"] >= 5).astype(int)
    hauls = (
        match_bowl.groupby(agg_group)
        .agg(four_wicket_hauls=("is_4w", "sum"), five_wicket_hauls=("is_5w", "sum"))
        .reset_index()
    )
    season_bowl = season_bowl.merge(hauls, on=agg_group, how="left")

    # ── Rename to schema ──
    rename = {"bowler": "player_name"}
    if team_col:
        rename[team_col] = "team"
    season_bowl = season_bowl.rename(columns=rename)
    if "team" not in season_bowl.columns:
        season_bowl["team"] = "Unknown"

    int_cols = ["innings_bowled", "balls_bowled", "runs_conceded",
                "wickets", "four_wicket_hauls", "five_wicket_hauls"]
    season_bowl[int_cols] = season_bowl[int_cols].fillna(0).astype(int)

    log.info(f"  Bowling stat rows: {len(season_bowl):,}")
    log.info(f"  Economy range    : {season_bowl['economy_rate'].min():.2f}–{season_bowl['economy_rate'].max():.2f}")
    return season_bowl


# ── Step 6: Save to MySQL ─────────────────────────────────────────────────────

def _to_python(val):
    """Convert numpy scalars → native Python for mysql-connector."""
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
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
    rows = [tuple(_to_python(row[c]) for c in cols) for _, row in df.iterrows()]
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
    rows = [tuple(_to_python(row[c]) for c in cols) for _, row in df.iterrows()]
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
    log.info(f"  Null bat_average  : {batting['batting_average'].isna().sum():,}  (never dismissed)")
    log.info(
        f"  Top 5 by runs:\n"
        + batting.nlargest(5, "runs_scored")[
            ["player_name", "season", "team", "runs_scored", "strike_rate", "batting_average"]
        ].to_string(index=False)
    )

    log.info("\n▶ BOWLING STATS")
    log.info(f"  Total rows        : {len(bowling):,}")
    log.info(f"  Unique bowlers    : {bowling['player_name'].nunique():,}")
    log.info(f"  Null economy_rate : {bowling['economy_rate'].isna().sum():,}")
    log.info(f"  Null bowl_average : {bowling['bowling_average'].isna().sum():,}  (0-wicket seasons)")
    log.info(
        f"  Top 5 by wickets:\n"
        + bowling.nlargest(5, "wickets")[
            ["player_name", "season", "team", "wickets", "economy_rate", "bowling_average"]
        ].to_string(index=False)
    )
    log.info(sep)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("═" * 60)
    log.info("IPL Transform — Phase 1 #3: Analytics Layer")
    log.info("═" * 60)

    # 1. Load
    matches_raw, deliveries_raw = load_raw()

    # 2. Clean
    matches_clean    = clean_matches(matches_raw)
    deliveries_clean = clean_deliveries(deliveries_raw, matches_clean)

    # 3. Engineer features
    batting_stats = build_batting_stats(deliveries_clean)
    bowling_stats = build_bowling_stats(deliveries_clean)

    # 4. In-memory validation
    print_validation_summary(batting_stats, bowling_stats)

    # 5. Connect to DB
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        log.info(f"\nConnected to MySQL: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    except Error as exc:
        log.error(f"DB connection failed: {exc}")
        sys.exit(1)

    # 6. Create tables + insert
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

    # 7. Final count check
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

    log.info("\nDone! Run setup_eda.py → python run_eda.py to generate the EDA report.")


if __name__ == "__main__":
    main()
