import os
import warnings

import joblib
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from config import (BIG_SIX, HISTORICAL_FILE, MODEL_DIR, MODEL_FILE,
                    PL_STANDINGS)
from sklearn.model_selection import cross_val_score, KFold


def process_data():
    print("Loading historical data...")
    try:
        df = pd.read_csv(HISTORICAL_FILE)
    except FileNotFoundError:
        print(f"Error: File not found at {HISTORICAL_FILE}")
        return None

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    matches = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"]).copy()

    # Enriched Features: Add League Position and Points
    def get_team_stats(team):
        stats = PL_STANDINGS.get(team, {"pos": 10, "points": 40})
        return stats["pos"], stats["points"]

    matches[["HomePos", "HomePts"]] = matches["HomeTeam"].apply(lambda x: pd.Series(get_team_stats(x)))
    matches[["AwayPos", "AwayPts"]] = matches["AwayTeam"].apply(lambda x: pd.Series(get_team_stats(x)))

    # Simplified Features to prevent overfitting: Use Relative Differences
    # pos_diff: lower is better (Home is higher in table)
    matches["pos_diff"] = matches["HomePos"] - matches["AwayPos"]
    # pts_diff: higher is better (Home has more points)
    matches["pts_diff"] = matches["HomePts"] - matches["AwayPts"]

    X = matches[["pos_diff", "pts_diff"]]
    y = matches["FTR"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Weights: Recent form and Big Six relevance
    weights = []
    current_date = pd.to_datetime("2026-03-21")

    for _, row in matches.iterrows():
        w = 1.0
        is_big_six = row["HomeTeam"] in BIG_SIX and row["AwayTeam"] in BIG_SIX
        days_old = (current_date - row["Date"]).days

        if is_big_six: w *= 1.5
        if days_old < 365: w *= 2.0

        weights.append(w)

    return X_scaled, y, weights, scaler


def train():
    result = process_data()
    if result is None:
        return

    X, y, weights, scaler = result

    # 1. K-Fold Cross Validation (10-Fold)
    print("Performing 10-Fold Cross-Validation...")
    kf = KFold(n_splits=10, shuffle=True, random_state=42)
    
    # Highly Regularized Model to prevent memorizing the small (87 match) dataset
    cv_model = LogisticRegression(
        C=0.01, 
        penalty='l2', 
        solver='lbfgs', 
        max_iter=1000, 
        class_weight='balanced'
    )
    
    cv_scores = cross_val_score(cv_model, X, y, cv=kf, scoring='accuracy')
    mean_accuracy = cv_scores.mean()
    std_accuracy = cv_scores.std()

    # Training on full set for final performance and saving
    full_model = LogisticRegression(C=0.01, penalty='l2', solver='lbfgs', max_iter=1000, class_weight='balanced')
    full_model.fit(X, y, sample_weight=weights)
    full_train_acc = accuracy_score(y, full_model.predict(X))

    print("-" * 40)
    print("ENHANCED MODEL TRAINING REPORT")
    print("-" * 40)
    print(f"Data Info : {len(X)} historical matches processed.")
    print(f"Features  : Teams, League Position, Points (Relative)")
    print(f"Algorithm : Logistic Regression (Optimized)")
    print("-" * 40)
    print(f"Prediction Score / Training Accuracy: {full_train_acc * 100:.1f}%")
    print(f"Validation Accuracy: {mean_accuracy * 100:.1f}%")
    print("-" * 40)
    print("Retraining on full dataset for maximum performance...")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": full_model, "scaler": scaler, "label_encoder": None}, MODEL_FILE)
    print(f"SUCCESS: Enhanced Prediction Model saved to {MODEL_FILE}")


if __name__ == "__main__":
    train()
