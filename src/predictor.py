# src/predictor.py MAINLY for the prediction midel into main srategy so it works into main 
import os
from datetime import date

import joblib
import pandas as pd

from config import (BIG_SIX, FIXTURE_FILE, HISTORICAL_FILE, MANAGERS,
                     MODEL_FILE, PL_STANDINGS)


class Predictor:
    def __init__(self):
        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError("Model not found. Run train_model.py first.")

        artifacts = joblib.load(MODEL_FILE)
        self.model = artifacts["model"]
        self.scaler = artifacts["scaler"]
        # Label encoder is no longer used for features, but may be present in old models
        self.le = artifacts.get("label_encoder") 
        self.fixtures = pd.read_csv(FIXTURE_FILE)

    def find_next_derby(self, user_team):
        df = self.fixtures.dropna(subset=["HomeTeam", "AwayTeam"]).copy()

        # Filter to Big Six derbies involving this team
        matches = df[
            ((df["HomeTeam"] == user_team) | (df["AwayTeam"] == user_team))
            & (df["HomeTeam"].isin(BIG_SIX))
            & (df["AwayTeam"].isin(BIG_SIX))
        ].copy()

        # Primary: filter by Status == "upcoming"
        upcoming = matches[matches["Status"] == "upcoming"] if "Status" in matches.columns else pd.DataFrame()
        if not upcoming.empty:
            return upcoming.iloc[0]

        # Fallback: filter by date (any fixture after today)
        if "Date" in matches.columns:
            today_str = date.today().isoformat()
            try:
                # Handle both %Y and %y formats
                fmt = "%Y-%m-%d" if len(matches["Date"].iloc[0].split('-')[0]) == 4 else "%y-%m-%d"
                matches["_date_parsed"] = pd.to_datetime(
                    matches["Date"], format=fmt, errors="coerce"
                )
                future = matches[
                    matches["_date_parsed"] >= pd.Timestamp(today_str)
                ].sort_values("_date_parsed")
                if not future.empty:
                    return future.iloc[0]
            except Exception:
                pass

        return None

    def get_h2h(self, team1, team2):
        df = pd.read_csv(HISTORICAL_FILE)
        # Filter matches between these two teams
        m = df[
            ((df["HomeTeam"] == team1) & (df["AwayTeam"] == team2)) |
            ((df["HomeTeam"] == team2) & (df["AwayTeam"] == team1))
        ]
        
        counts = {"home_wins": 0, "away_wins": 0, "draws": 0, "total": len(m)}
        for _, row in m.iterrows():
            if row["FTR"] == "D":
                counts["draws"] += 1
            elif row["HomeTeam"] == team1:
                if row["FTR"] == "H": counts["home_wins"] += 1
                else: counts["away_wins"] += 1
            else: # HomeTeam == team2
                if row["FTR"] == "H": counts["away_wins"] += 1
                else: counts["home_wins"] += 1
        
        return counts

    def predict_match(self, home_team, away_team):
        # 1. Get stats for relative features
        h_stats = PL_STANDINGS.get(home_team, {"pos": 10, "points": 40})
        a_stats = PL_STANDINGS.get(away_team, {"pos": 10, "points": 40})

        # 2. Calculate Relative Differences (matching train_model.py)
        pos_diff = h_stats["pos"] - a_stats["pos"]
        pts_diff = h_stats["points"] - a_stats["points"]

        # 3. Create a DataFrame with the correct feature names
        feature_names = ["pos_diff", "pts_diff"]
        features_df = pd.DataFrame([[pos_diff, pts_diff]], columns=feature_names)

        # 4. Run Model
        # Now we transform the DataFrame, which has the feature names
        scaled_features = self.scaler.transform(features_df)
        probs = self.model.predict_proba(scaled_features)[0]
        classes = self.model.classes_

        results = {cls: prob for cls, prob in zip(classes, probs)}

        return {
            "home_win": results.get("H", 0.0),
            "draw": results.get("D", 0.0),
            "away_win": results.get("A", 0.0),
            "home_manager": MANAGERS.get(home_team, "Unknown"),
            "away_manager": MANAGERS.get(away_team, "Unknown"),
            "confidence": max(results.values()),
        }
