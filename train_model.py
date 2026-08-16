"""
IPL Win Probability Model Training Script
===========================================
Trains Logistic Regression and XGBoost models to predict win probability
for the chasing team (2nd innings) in IPL matches.

Features used:
  - current_runs
  - wickets_fallen
  - overs_completed
  - target
  - venue
  - batting_team
  - bowling_team

Target variable:
  - result (1 if chasing/batting team won, 0 otherwise)

Saves the best performing model to python_service/models/win_probability_model.pkl
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier

# Force UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Team Name Aliases Standardisation ──────────────────────────────────────────
TEAM_ALIASES = {
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


def normalize_team(name):
    if not isinstance(name, str) or name.strip() in ("", "nan", "None"):
        return "Unknown"
    return TEAM_ALIASES.get(name.strip(), name.strip())


def load_and_preprocess_data():
    raw_dir = Path("ipl_data_raw")
    matches_path = raw_dir / "matches.csv"
    deliveries_path = raw_dir / "deliveries.csv"

    print("Loading raw CSV files...")
    matches = pd.read_csv(matches_path)
    deliveries = pd.read_csv(deliveries_path)

    print(f"Loaded {len(matches)} matches and {len(deliveries)} delivery records.")

    # 1. Standardize team names
    matches["team1"] = matches["team1"].apply(normalize_team)
    matches["team2"] = matches["team2"].apply(normalize_team)
    matches["winner"] = matches["winner"].apply(normalize_team)
    deliveries["batting_team"] = deliveries["batting_team"].apply(normalize_team)
    deliveries["bowling_team"] = deliveries["bowling_team"].apply(normalize_team)

    # 2. Compute 1st Innings total score to determine target
    first_innings = deliveries[deliveries["inning"] == 1]
    first_innings_summary = (
        first_innings.groupby("match_id")["total_runs"]
        .sum()
        .reset_index()
        .rename(columns={"total_runs": "first_innings_runs"})
    )
    first_innings_summary["target"] = first_innings_summary["first_innings_runs"] + 1

    # Merge target into matches dataset
    matches = matches.merge(first_innings_summary[["match_id", "target"]], left_on="id", right_on="match_id", how="inner")

    # 3. Filter deliveries for 2nd innings (chasing team)
    chase_deliveries = deliveries[deliveries["inning"] == 2].copy()
    chase_deliveries = chase_deliveries.merge(
        matches[["id", "venue", "winner", "target"]],
        left_on="match_id",
        right_on="id",
        how="inner",
    )

    # Filter valid matches with a valid winner and target
    chase_deliveries = chase_deliveries[
        (chase_deliveries["winner"] != "Unknown") &
        (chase_deliveries["target"] > 0)
    ].copy()

    # Target label: 1 if batting team (chaser) won the match, else 0
    chase_deliveries["result"] = (
        chase_deliveries["batting_team"] == chase_deliveries["winner"]
    ).astype(int)

    # 4. Feature engineering per delivery
    # Calculate cumulative runs and wickets fallen in 2nd innings
    chase_deliveries["current_runs"] = (
        chase_deliveries.groupby("match_id")["total_runs"].cumsum()
    )
    
    # Check if is_wicket column exists and cumulative count of wickets
    if "is_wicket" in chase_deliveries.columns:
        chase_deliveries["wickets_fallen"] = (
            chase_deliveries.groupby("match_id")["is_wicket"].cumsum()
        )
    else:
        chase_deliveries["is_wicket"] = chase_deliveries["player_dismissed"].notna().astype(int)
        chase_deliveries["wickets_fallen"] = (
            chase_deliveries.groupby("match_id")["is_wicket"].cumsum()
        )

    # Overs completed calculation: (over * 6 + ball) / 6.0
    # Over in dataset is 0-indexed (0 to 19), ball is 1 to 6+
    chase_deliveries["overs_completed"] = (
        chase_deliveries["over"] + (chase_deliveries["ball"] / 6.0)
    )

    # Select final feature columns
    features = [
        "current_runs",
        "wickets_fallen",
        "overs_completed",
        "target",
        "venue",
        "batting_team",
        "bowling_team",
    ]

    df = chase_deliveries[features + ["result"]].dropna()

    print(f"Processed dataset ready: {len(df)} samples across 2nd innings deliveries.")
    return df, features


def train_and_evaluate_models(df, features):
    X = df[features]
    y = df["result"]

    categorical_cols = ["venue", "batting_team", "bowling_team"]
    numerical_cols = ["current_runs", "wickets_fallen", "overs_completed", "target"]

    # Stratified train/test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")

    # Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_cols),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_cols,
            ),
        ]
    )

    # 1. Logistic Regression Model Pipeline
    lr_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )

    # 2. XGBoost Model Pipeline
    xgb_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42,
                    eval_metric="logloss",
                ),
            ),
        ]
    )

    # --- Train Logistic Regression ---
    print("\n" + "=" * 60)
    print("Training Logistic Regression Model...")
    print("=" * 60)
    lr_pipeline.fit(X_train, y_train)
    y_pred_lr = lr_pipeline.predict(X_test)
    acc_lr = accuracy_score(y_test, y_pred_lr)

    print(f"\n[Logistic Regression] Test Accuracy: {acc_lr:.4f} ({acc_lr * 100:.2f}%)")
    print("\n[Logistic Regression] Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_lr))
    print("\n[Logistic Regression] Classification Report:")
    print(classification_report(y_test, y_pred_lr, digits=4))

    # --- Train XGBoost ---
    print("\n" + "=" * 60)
    print("Training XGBoost Classifier Model...")
    print("=" * 60)
    xgb_pipeline.fit(X_train, y_train)
    y_pred_xgb = xgb_pipeline.predict(X_test)
    acc_xgb = accuracy_score(y_test, y_pred_xgb)

    print(f"\n[XGBoost] Test Accuracy: {acc_xgb:.4f} ({acc_xgb * 100:.2f}%)")
    print("\n[XGBoost] Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_xgb))
    print("\n[XGBoost] Classification Report:")
    print(classification_report(y_test, y_pred_xgb, digits=4))

    # --- Compare & Save Best Model ---
    print("\n" + "=" * 60)
    print("MODEL COMPARISON & EXPORT")
    print("=" * 60)
    print(f"Logistic Regression Accuracy: {acc_lr * 100:.2f}%")
    print(f"XGBoost Accuracy:             {acc_xgb * 100:.2f}%")

    if acc_xgb >= acc_lr:
        best_model_name = "XGBoost"
        best_pipeline = xgb_pipeline
        best_acc = acc_xgb
    else:
        best_model_name = "Logistic Regression"
        best_pipeline = lr_pipeline
        best_acc = acc_lr

    print(f"\n>>> Selected Best Model: {best_model_name} (Accuracy: {best_acc * 100:.2f}%)")

    # Save best model to python_service/models/win_probability_model.pkl
    output_dir = Path("python_service") / "models"
    os.makedirs(output_dir, exist_ok=True)
    model_path = output_dir / "win_probability_model.pkl"

    joblib.dump(best_pipeline, model_path)
    print(f"Successfully saved trained {best_model_name} pipeline to: {model_path.resolve()}")


if __name__ == "__main__":
    df, features = load_and_preprocess_data()
    train_and_evaluate_models(df, features)
