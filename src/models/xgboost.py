import os
import joblib
import pandas as pd
import xgboost as xgb

class MatchGoalPredictor:
    def __init__(self):
        self.home_model = None
        self.away_model = None

        pass

    # feature columns (stats that this model will use to predict how many goals scored)
    '''
        Team A vs Team B

        For each team:
        - Goals scored
        - Goals conceded
        - Home Form (Total)
        - Away Form (Total)
        - Overall Form (last 5 games)
        - Shots per posession ratio (last 5 games)
        - Home Advantage
    '''

    def train_and_save(self, df: pd.DataFrame, feature_cols: list[str]):
        # X is features, y is target
        X = df[feature_cols]
        y_home = df["HomeGoals"]
        y_away = df["AwayGoals"]
        
        # uses count poisson to estimate goals to prevent negative goals
        self.home_model = xgb.XGBRegressor(
            objective="count:poisson",
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4

        )
        self.home_model.fit(X, y_home)

        self.away_model = xgb.XGBRegressor(
            objective="count:poisson",
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4
        )
        self.away_model.fit(X, y_away)
        
        os.makedirs("models_saved", exist_ok=True)

        # save both models to disk
        joblib.dump(self.home_model, "models_saved/xgb_home.pkl")
        joblib.dump(self.away_model, "models_saved/xgb_away.pkl")

        pass

    def predict_xg(self, match_features: pd.DataFrame) -> tuple[float, float]:
        home_xg = float(self.home_model.predict(match_features)[0])
        away_xg = float(self.away_model.predict(match_features)[0])

        return (home_xg, away_xg)