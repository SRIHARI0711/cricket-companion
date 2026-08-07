"""
IPL Dataset Loader — Phase 1: Data Foundation
Downloads the IPL dataset from Kaggle and loads it into the existing
cricket_companion MySQL database (teams, players, series, matches, scorecards).

Usage:
    1. Set KAGGLE_USERNAME and KAGGLE_KEY in your .env file (or export as env vars).
       Get your API key from https://www.kaggle.com/settings → API → Create New Token.
    2. Set DB_PASSWORD in your .env (or it defaults to prompting).
    3. Run:  python load_ipl_data.py
"""

import os
import sys
import json
import zipfile
import shutil
import logging
import getpass
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),   # set in .env or prompted below
    "database": os.getenv("DB_NAME", "cricket_companion"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}

KAGGLE_DATASET   = "patrickb1912/ipl-complete-dataset-20082020"   # primary
FALLBACK_DATASET = "nowke9/ipldata"                                # backup
DOWNLOAD_DIR     = Path("ipl_data_raw")

# ── Kaggle auth setup ─────────────────────────────────────────────────────────

def setup_kaggle_auth() -> bool:
    """Write kaggle.json from env vars if the file doesn't already exist."""
    kaggle_dir = Path.home() / ".config" / "kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"

    if kaggle_json.exists():
        log.info("kaggle.json already present — skipping auth setup.")
        return True

    username = os.getenv("KAGGLE_USERNAME", "").strip()
    key      = os.getenv("KAGGLE_KEY", "").strip()

    if not username or not key:
        log.error(
            "Kaggle credentials not found.\n"
            "  Option A: add KAGGLE_USERNAME and KAGGLE_KEY to your .env file.\n"
            "  Option B: download kaggle.json from https://www.kaggle.com/settings\n"
            "            and place it at ~/.config/kaggle/kaggle.json"
        )
        return False

    kaggle_dir.mkdir(parents=True, exist_ok=True)
    kaggle_json.write_text(json.dumps({"username": username, "key": key}))
    kaggle_json.chmod(0o600)
    log.info("kaggle.json written successfully.")
    return True


def download_dataset(dataset: str, dest: Path) -> bool:
    """Download and unzip a Kaggle dataset into dest/."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()

        dest.mkdir(parents=True, exist_ok=True)
        log.info(f"Downloading dataset '{dataset}' …")
        api.dataset_download_files(dataset, path=str(dest), unzip=True)
        log.info(f"Dataset saved to {dest}/")
        return True
    except Exception as exc:
        log.warning(f"Download failed for '{dataset}': {exc}")
        return False

# ── CSV discovery ─────────────────────────────────────────────────────────────

def find_csv(folder: Path, keywords: list[str]) -> Path | None:
    """Return the first CSV whose filename contains any of the keywords."""
    for csv in sorted(folder.rglob("*.csv")):
        name = csv.stem.lower()
        if any(kw in name for kw in keywords):
            return csv
    return None

# ── DB helpers ────────────────────────────────────────────────────────────────

def get_connection():
    cfg = DB_CONFIG.copy()
    if not cfg["password"]:
        cfg["password"] = getpass.getpass("MySQL password for root@localhost: ")
    conn = mysql.connector.connect(**cfg)
    conn.autocommit = False
    return conn


def execute_many(cursor, sql: str, rows: list[tuple], label: str) -> int:
    if not rows:
        log.warning(f"  No rows to insert for {label}.")
        return 0
    cursor.executemany(sql, rows)
    log.info(f"  ✓ {label}: {cursor.rowcount} rows inserted.")
    return cursor.rowcount


def fetch_map(cursor, table: str, key_col: str, val_col: str = "id") -> dict:
    cursor.execute(f"SELECT {key_col}, {val_col} FROM {table}")
    return {row[0]: row[1] for row in cursor.fetchall()}

# ── Data cleaners ─────────────────────────────────────────────────────────────

def clean_str(val, default="Unknown") -> str:
    if pd.isna(val) or str(val).strip() in ("", "nan", "None"):
        return default
    return str(val).strip()


def clean_int(val, default=0) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def normalize_team(name: str) -> str:
    """Collapse historical franchise renames to a single canonical name."""
    aliases = {
        "Delhi Daredevils":            "Delhi Capitals",
        "Deccan Chargers":             "Sunrisers Hyderabad",
        "Pune Warriors":               "Rising Pune Supergiant",
        "Rising Pune Supergiants":     "Rising Pune Supergiant",
        "Kings XI Punjab":             "Punjab Kings",
        "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    }
    return aliases.get(name.strip(), name.strip())

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_teams(cursor, matches_df: pd.DataFrame) -> dict:
    """Insert teams that don't yet exist; return name→id map."""
    existing = fetch_map(cursor, "teams", "team_name")

    team_names = set()
    for col in ("team1", "team2", "toss_winner", "winner"):
        if col in matches_df.columns:
            team_names.update(matches_df[col].dropna().unique())

    new_teams = [
        (normalize_team(t), "Unknown", "Unknown")
        for t in team_names
        if normalize_team(t) not in existing
    ]

    if new_teams:
        execute_many(
            cursor,
            "INSERT IGNORE INTO teams (team_name, coach, captain) VALUES (%s, %s, %s)",
            new_teams,
            "teams",
        )

    return fetch_map(cursor, "teams", "team_name")


def load_series(cursor, matches_df: pd.DataFrame) -> dict:
    """Insert one series row per IPL season; return season→id map."""
    existing_names = fetch_map(cursor, "series", "series_name")

    seasons = sorted(matches_df["season"].dropna().unique()) if "season" in matches_df else []
    rows = []
    for season in seasons:
        name = f"IPL {season}"
        if name in existing_names:
            continue
        season_data = matches_df[matches_df["season"] == season]
        start = (
            pd.to_datetime(season_data["date"], errors="coerce").min().date()
            if "date" in season_data.columns else None
        )
        end = (
            pd.to_datetime(season_data["date"], errors="coerce").max().date()
            if "date" in season_data.columns else None
        )
        rows.append((name, start, end, "Completed"))

    if rows:
        execute_many(
            cursor,
            "INSERT IGNORE INTO series (series_name, start_date, end_date, status) VALUES (%s, %s, %s, %s)",
            rows,
            "series",
        )

    # Return season-year → series_id (e.g. "2008" → 5)
    all_series = {}
    cursor.execute("SELECT series_name, id FROM series")
    for sname, sid in cursor.fetchall():
        if sname.startswith("IPL "):
            all_series[sname[4:]] = sid   # key = "2008", "2009", …
    return all_series


def load_matches(cursor, matches_df: pd.DataFrame, team_map: dict, series_map: dict) -> dict:
    """Insert matches; return original-id → new DB id map."""
    existing_ids = set()
    cursor.execute("SELECT id FROM matches")
    for (mid,) in cursor.fetchall():
        existing_ids.add(mid)

    rows = []
    id_map = {}       # kaggle match id → db match id (will be filled after insert)

    # We'll track inserts to build the id_map after commit
    insert_order = []

    for _, row in matches_df.iterrows():
        t1 = normalize_team(clean_str(row.get("team1", "")))
        t2 = normalize_team(clean_str(row.get("team2", "")))
        season = str(clean_str(row.get("season", "")))

        t1_id     = team_map.get(t1)
        t2_id     = team_map.get(t2)
        series_id = series_map.get(season)

        winner_name = clean_str(row.get("winner", ""), "")
        winner_id   = team_map.get(normalize_team(winner_name)) if winner_name else None

        match_date = None
        if "date" in row and pd.notna(row["date"]):
            try:
                match_date = pd.to_datetime(row["date"]).date()
            except Exception:
                pass

        venue = clean_str(row.get("venue", row.get("city", "")), "Unknown")

        if not t1_id or not t2_id:
            continue   # skip if teams couldn't be resolved

        rows.append((series_id, t1_id, t2_id, match_date, venue, winner_id))
        insert_order.append(row.get("id") or row.get("match_id"))

    execute_many(
        cursor,
        "INSERT INTO matches (series_id, team1_id, team2_id, match_date, venue, winner_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        rows,
        "matches",
    )

    # Rebuild id_map from last_insert_id range
    if rows:
        cursor.execute("SELECT id FROM matches ORDER BY id DESC LIMIT %s", (len(rows),))
        new_ids = [r[0] for r in cursor.fetchall()][::-1]
        for kaggle_id, db_id in zip(insert_order, new_ids):
            if kaggle_id is not None:
                id_map[str(int(kaggle_id))] = db_id

    return id_map


def load_players(cursor, deliveries_df: pd.DataFrame, team_map: dict) -> dict:
    """
    Infer players from the deliveries file (batter, bowler, non_striker cols).
    Insert those not already in the DB. Return name→id map.
    """
    existing = fetch_map(cursor, "players", "name")

    player_names = set()
    for col in ("batter", "batsman", "bowler", "non_striker"):
        if col in deliveries_df.columns:
            player_names.update(deliveries_df[col].dropna().unique())

    new_players = []
    for name in sorted(player_names):
        if name not in existing:
            # We can't reliably determine role from deliveries alone,
            # so default to 'Batsman'; you can update later.
            new_players.append((name.strip(), None, "Batsman", None))

    if new_players:
        execute_many(
            cursor,
            "INSERT IGNORE INTO players (name, age, role, team) VALUES (%s, %s, %s, %s)",
            new_players,
            "players",
        )

    return fetch_map(cursor, "players", "name")


def load_scorecards(cursor, deliveries_df: pd.DataFrame, player_map: dict, match_id_map: dict):
    """
    Aggregate deliveries into per-player-per-match scorecards and insert them.

    Batting: sum runs_batter → runs_scored, count deliveries → balls_faced
    Bowling: count wickets (excluding run-out) → wickets_taken
    """
    # normalise column names across dataset versions
    col_map = {
        "batsman":          "batter",
        "batsman_runs":     "batsman_runs",
        "runs_off_bat":     "batsman_runs",
        "player_dismissed": "player_dismissed",
        "dismissal_kind":   "dismissal_kind",
        "match_id":         "match_id",
        "id":               "match_id",
    }
    df = deliveries_df.rename(columns={k: v for k, v in col_map.items() if k in deliveries_df.columns})

    # Identify the match-id column
    mid_col = "match_id" if "match_id" in df.columns else "id"

    # ── Batting stats ──
    bat_col  = "batter" if "batter" in df.columns else "batsman"
    runs_col = next((c for c in ["batsman_runs", "runs_off_bat"] if c in df.columns), None)

    if bat_col not in df.columns or runs_col not in df.columns:
        log.warning("Could not find batting columns in deliveries — skipping scorecards.")
        return

    batting = (
        df.groupby([mid_col, bat_col])
        .agg(runs_scored=(runs_col, "sum"), balls_faced=(runs_col, "count"))
        .reset_index()
    )

    # ── Bowling stats ──
    wicket_col = next((c for c in ["player_dismissed", "is_wicket"] if c in df.columns), None)
    dismissal_col = "dismissal_kind" if "dismissal_kind" in df.columns else None

    if wicket_col and "bowler" in df.columns:
        if df[wicket_col].dtype == object:  # player_dismissed: non-empty = wicket
            wdf = df[df[wicket_col].notna() & (df[wicket_col] != "")]
        else:                               # is_wicket: 1 = wicket
            wdf = df[df[wicket_col] == 1]

        # Exclude run-outs (bowler not credited)
        if dismissal_col:
            wdf = wdf[wdf[dismissal_col] != "run out"]

        bowling = (
            wdf.groupby([mid_col, "bowler"])
            .size()
            .reset_index(name="wickets_taken")
        )
    else:
        bowling = pd.DataFrame(columns=[mid_col, "bowler", "wickets_taken"])

    # ── Merge batting + bowling ──
    batting  = batting.rename(columns={bat_col: "player_name"})
    bowling  = bowling.rename(columns={"bowler": "player_name"})

    merged = pd.merge(batting, bowling, on=[mid_col, "player_name"], how="outer")
    merged["runs_scored"]    = merged["runs_scored"].fillna(0).astype(int)
    merged["balls_faced"]    = merged["balls_faced"].fillna(0).astype(int)
    merged["wickets_taken"]  = merged["wickets_taken"].fillna(0).astype(int)

    rows = []
    skipped = 0
    for _, r in merged.iterrows():
        kaggle_mid = str(int(float(r[mid_col]))) if pd.notna(r[mid_col]) else None
        db_mid     = match_id_map.get(kaggle_mid)
        player_id  = player_map.get(str(r["player_name"]).strip())

        if not db_mid or not player_id:
            skipped += 1
            continue

        rows.append((player_id, db_mid, int(r["runs_scored"]), int(r["balls_faced"]), int(r["wickets_taken"])))

    if skipped:
        log.warning(f"  Skipped {skipped} scorecard rows (unresolved match/player id).")

    execute_many(
        cursor,
        "INSERT INTO scorecards (player_id, match_id, runs_scored, balls_faced, wickets_taken) "
        "VALUES (%s, %s, %s, %s, %s)",
        rows,
        "scorecards",
    )

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("═" * 60)
    log.info("IPL Data Loader — Phase 1: Data Foundation")
    log.info("═" * 60)

    # 1. Kaggle auth
    if not setup_kaggle_auth():
        sys.exit(1)

    # 2. Download dataset
    success = download_dataset(KAGGLE_DATASET, DOWNLOAD_DIR)
    if not success:
        log.info(f"Trying fallback dataset: {FALLBACK_DATASET}")
        success = download_dataset(FALLBACK_DATASET, DOWNLOAD_DIR)
    if not success:
        log.error(
            "Both datasets failed to download.\n"
            "Manual fallback:\n"
            "  1. Go to https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020\n"
            "  2. Download and unzip into a folder named 'ipl_data_raw/'\n"
            "  3. Re-run this script."
        )
        sys.exit(1)

    # 3. Locate CSVs
    matches_csv     = find_csv(DOWNLOAD_DIR, ["match"])
    deliveries_csv  = find_csv(DOWNLOAD_DIR, ["deliver", "ball"])

    if not matches_csv:
        log.error(f"Could not find matches CSV in {DOWNLOAD_DIR}/. Files present:")
        for f in DOWNLOAD_DIR.rglob("*.csv"):
            log.error(f"  {f}")
        sys.exit(1)

    log.info(f"Matches CSV    : {matches_csv}")
    log.info(f"Deliveries CSV : {deliveries_csv or 'NOT FOUND — scorecards will be skipped'}")

    # 4. Load CSVs
    matches_df    = pd.read_csv(matches_csv)
    deliveries_df = pd.read_csv(deliveries_csv) if deliveries_csv else None

    log.info(f"Matches rows   : {len(matches_df):,}")
    if deliveries_df is not None:
        log.info(f"Deliveries rows: {len(deliveries_df):,}")

    # 5. Connect to DB
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        log.info(f"Connected to MySQL: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    except Error as exc:
        log.error(f"DB connection failed: {exc}")
        sys.exit(1)

    # 6. Load in dependency order
    try:
        log.info("\n── Teams ─────────────────────────────────────────")
        team_map = load_teams(cursor, matches_df)

        log.info("\n── Series ────────────────────────────────────────")
        series_map = load_series(cursor, matches_df)

        log.info("\n── Matches ───────────────────────────────────────")
        match_id_map = load_matches(cursor, matches_df, team_map, series_map)

        if deliveries_df is not None:
            log.info("\n── Players ───────────────────────────────────────")
            player_map = load_players(cursor, deliveries_df, team_map)

            log.info("\n── Scorecards ────────────────────────────────────")
            load_scorecards(cursor, deliveries_df, player_map, match_id_map)
        else:
            log.warning("Deliveries CSV not found — players and scorecards skipped.")

        conn.commit()
        log.info("\n✅ All data committed successfully.")

    except Exception as exc:
        conn.rollback()
        log.error(f"Error during load — rolling back: {exc}")
        raise
    finally:
        cursor.close()
        conn.close()

    # 7. Summary
    log.info("\n── Final row counts ──────────────────────────────")
    try:
        conn2   = get_connection()
        cur2    = conn2.cursor()
        for tbl in ("teams", "players", "series", "matches", "scorecards"):
            cur2.execute(f"SELECT COUNT(*) FROM {tbl}")
            (n,) = cur2.fetchone()
            log.info(f"  {tbl:<14}: {n:>7,} rows")
        cur2.close()
        conn2.close()
    except Exception:
        pass

    log.info("\nDone! Your cricket_companion DB is loaded with IPL data.")


if __name__ == "__main__":
    main()
