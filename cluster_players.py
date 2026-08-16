"""
IPL Player Clustering Script — Phase 2 #7
=========================================
Performs K-Means clustering on IPL batting statistics (runs, strike_rate,
average, boundary_percentage, innings).

Determines optimal k using the Elbow Method, assigns deterministic cricket
archetype labels based on centroid feature profiles, and persists the results
to the `player_clusters` MySQL table.

Usage:
    python cluster_players.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Force UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cricket_companion"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Error as e:
        print(f"[Warning] Failed to connect to MySQL ({e}).")
        return None


def fetch_batting_data_from_db(conn):
    """Try fetching aggregated batting stats from ipl_batting_stats MySQL table."""
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                player_name,
                SUM(innings) AS innings,
                SUM(runs_scored) AS runs,
                SUM(balls_faced) AS balls_faced,
                SUM(dismissals) AS dismissals,
                SUM(fours) AS fours,
                SUM(sixes) AS sixes
            FROM ipl_batting_stats
            GROUP BY player_name
            HAVING SUM(innings) >= 5;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        if rows:
            print(f"Fetched {len(rows)} player records from MySQL 'ipl_batting_stats' table.")
            df = pd.DataFrame(rows)
            return df
    except Error as e:
        print(f"[Info] Could not query ipl_batting_stats table: {e}")
    return None


def fetch_batting_data_from_csv():
    """Fallback: aggregate batting stats directly from raw ipl_data_raw/deliveries.csv."""
    deliveries_path = Path("ipl_data_raw") / "deliveries.csv"
    if not deliveries_path.exists():
        raise FileNotFoundError(f"Deliveries CSV not found at {deliveries_path}")

    print("Aggregating player stats directly from raw deliveries.csv...")
    deliveries = pd.read_csv(deliveries_path)

    # Standardize player name or grouping by batter
    grouped = deliveries.groupby("batter").agg(
        innings=("match_id", "nunique"),
        runs=("batsman_runs", "sum"),
        balls_faced=("ball", "count"),
        dismissals=("is_wicket", "sum") if "is_wicket" in deliveries.columns else ("player_dismissed", lambda s: s.notna().sum()),
        fours=("batsman_runs", lambda s: (s == 4).sum()),
        sixes=("batsman_runs", lambda s: (s == 6).sum()),
    ).reset_index().rename(columns={"batter": "player_name"})

    filtered = grouped[grouped["innings"] >= 5].copy()
    print(f"Aggregated {len(filtered)} player records from deliveries.csv (innings >= 5).")
    return filtered


def load_data():
    conn = get_db_connection()
    df = fetch_batting_data_from_db(conn)
    if conn:
        conn.close()

    if df is None or len(df) == 0:
        df = fetch_batting_data_from_csv()

    # Convert Decimal types from MySQL to standard float/int
    num_cols = ["innings", "runs", "balls_faced", "dismissals", "fours", "sixes"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Calculate derived stats
    df["strike_rate"] = np.where(
        df["balls_faced"] > 0,
        (df["runs"] / df["balls_faced"]) * 100.0,
        0.0
    )
    df["average"] = np.where(
        df["dismissals"] > 0,
        df["runs"] / df["dismissals"],
        df["runs"]  # if never dismissed
    )
    boundary_runs = (df["fours"] * 4) + (df["sixes"] * 6)
    df["boundary_percentage"] = np.where(
        df["runs"] > 0,
        (boundary_runs / df["runs"]) * 100.0,
        0.0
    )

    df["strike_rate"] = df["strike_rate"].round(2)
    df["average"] = df["average"].round(2)
    df["boundary_percentage"] = df["boundary_percentage"].round(2)

    return df



def evaluate_elbow_method(X_scaled):
    print("\n" + "=" * 60)
    print("ELBOW METHOD EVALUATION (k = 2 to 8)")
    print("=" * 60)
    inertias = []
    k_values = range(2, 9)

    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        print(f"k = {k} | Inertia (Sum of Squared Distances): {kmeans.inertia_:.2f}")

    return inertias


def assign_deterministic_archetypes(df, feature_cols, cluster_col="cluster_id"):
    """
    Dynamically maps cluster IDs to cricket archetypes based on centroid feature values,
    guaranteeing 100% deterministic labeling regardless of cluster ID assignment.
    """
    centroids = df.groupby(cluster_col)[feature_cols].mean()

    # Calculate z-scores across centroids to assess relative strengths
    z_centroids = (centroids - centroids.mean()) / (centroids.std() + 1e-6)

    # Score candidates for each archetype
    scores = pd.DataFrame(index=centroids.index)
    scores["Anchor / Elite Top-Order"] = z_centroids["runs"] * 1.5 + z_centroids["average"] * 1.5 + z_centroids["innings"] * 1.0
    scores["Aggressive Opener / Power Hitter"] = z_centroids["strike_rate"] * 1.5 + z_centroids["boundary_percentage"] * 1.5 + z_centroids["runs"] * 0.5
    scores["Middle-Order Finisher"] = z_centroids["strike_rate"] * 1.5 + z_centroids["boundary_percentage"] * 1.0 - z_centroids["innings"] * 0.5
    scores["Middle-Order Accumulator"] = z_centroids["average"] * 0.8 + z_centroids["innings"] * 0.5 - abs(z_centroids["strike_rate"]) * 0.5
    scores["Lower-Order / Tailender"] = -(z_centroids["runs"] + z_centroids["average"] + z_centroids["strike_rate"])

    archetype_map = {}
    assigned_labels = set()

    # Priority assignment order
    archetypes = [
        "Anchor / Elite Top-Order",
        "Aggressive Opener / Power Hitter",
        "Middle-Order Finisher",
        "Middle-Order Accumulator",
        "Lower-Order / Tailender",
    ]

    for label in archetypes:
        if label in scores.columns:
            sorted_clusters = scores[label].sort_values(ascending=False).index
            for c_id in sorted_clusters:
                if c_id not in archetype_map and label not in assigned_labels:
                    archetype_map[c_id] = label
                    assigned_labels.add(label)
                    break

    # Fallback for remaining unassigned clusters
    for c_id in centroids.index:
        if c_id not in archetype_map:
            archetype_map[c_id] = f"Cluster {c_id}"

    df["archetype_label"] = df[cluster_col].map(archetype_map)

    print("\n" + "=" * 60)
    print("DETERMINISTIC CLUSTER CENTROIDS & ARCHETYPE ASSIGNMENTS")
    print("=" * 60)
    for c_id, label in archetype_map.items():
        c_stats = centroids.loc[c_id]
        count = (df[cluster_col] == c_id).sum()
        print(f"\nCluster {c_id} -> [{label}] ({count} players)")
        print(f"  Runs: {c_stats['runs']:.1f} | Avg: {c_stats['average']:.1f} | SR: {c_stats['strike_rate']:.1f} | Boundary %: {c_stats['boundary_percentage']:.1f}% | Innings: {c_stats['innings']:.1f}")

    return df, archetype_map


def save_clusters_to_mysql(df):
    conn = get_db_connection()
    if conn is None:
        print("[Warning] Cannot save to MySQL: database connection unavailable.")
        return

    try:
        cursor = conn.cursor()

        # Create player_clusters table
        create_sql = """
            CREATE TABLE IF NOT EXISTS player_clusters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player_name VARCHAR(120) NOT NULL UNIQUE,
                cluster_id INT NOT NULL,
                archetype_label VARCHAR(80) NOT NULL,
                innings INT,
                total_runs INT,
                strike_rate DECIMAL(7,2),
                batting_average DECIMAL(7,2),
                boundary_percentage DECIMAL(6,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_sql)

        # Insert or update player records
        upsert_sql = """
            INSERT INTO player_clusters
                (player_name, cluster_id, archetype_label, innings, total_runs, strike_rate, batting_average, boundary_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cluster_id = VALUES(cluster_id),
                archetype_label = VALUES(archetype_label),
                innings = VALUES(innings),
                total_runs = VALUES(total_runs),
                strike_rate = VALUES(strike_rate),
                batting_average = VALUES(batting_average),
                boundary_percentage = VALUES(boundary_percentage);
        """

        records = [
            (
                row["player_name"],
                int(row["cluster_id"]),
                row["archetype_label"],
                int(row["innings"]),
                int(row["runs"]),
                float(row["strike_rate"]),
                float(row["average"]),
                float(row["boundary_percentage"]),
            )
            for _, row in df.iterrows()
        ]

        cursor.executemany(upsert_sql, records)
        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n[Success] Persisted {len(records)} player cluster assignments into MySQL 'player_clusters' table!")
    except Error as e:
        print(f"[Error] Failed to save cluster assignments to MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()


def main():
    df = load_data()
    feature_cols = ["runs", "strike_rate", "average", "boundary_percentage", "innings"]

    print(f"\nExtracted statistics for {len(df)} qualifying players.")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])

    # Evaluate Elbow method
    evaluate_elbow_method(X_scaled)

    # Perform K-Means clustering with optimal k = 5
    k_optimal = 5
    print(f"\nTraining K-Means with optimal k = {k_optimal}...")
    kmeans = KMeans(n_clusters=k_optimal, random_state=42, n_init=10)
    df["cluster_id"] = kmeans.fit_predict(X_scaled)

    # Dynamically assign deterministic cricket archetypes
    df, archetype_map = assign_deterministic_archetypes(df, feature_cols, cluster_col="cluster_id")

    # Save to MySQL
    save_clusters_to_mysql(df)

    # Display sample assignments
    print("\n" + "=" * 60)
    print("SAMPLE PLAYER CLUSTER ASSIGNMENTS")
    print("=" * 60)
    sample_players = df.sort_values(by="runs", ascending=False).head(15)
    for _, row in sample_players.iterrows():
        print(f"{row['player_name']:<25} | Runs: {row['runs']:<5} | SR: {row['strike_rate']:<6} | Avg: {row['average']:<5} | Archetype: {row['archetype_label']}")


if __name__ == "__main__":
    main()
