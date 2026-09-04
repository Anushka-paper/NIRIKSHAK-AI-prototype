import pandas as pd
import numpy as np
import os
import joblib

class XGBoostRiskScoringModel:
    def __init__(self):
        self.model = None

    def train(self, data: pd.DataFrame):
        print("Training XGBoost Risk Scoring Model (Simulation)...")
        self.model = "xgboost_model_trained"
        
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        joblib.dump(self, os.path.join(models_dir, 'xgboost_risk_scoring_model.joblib'))
        print("XGBoost Risk Scoring Model saved.")

    def predict_risk(self, signals: dict):
        """
        Takes signals from other models and outputs a composite risk.
        signals: {
            "is_anomaly": bool, 
            "delay_prob_365": float, 
            "duplicate_found": bool
        }
        """
        score = 0
        if signals.get("is_anomaly"): score += 40
        if signals.get("duplicate_found"): score += 50
        
        delay = signals.get("delay_prob_365", 0.95)
        if delay < 0.5: # i.e. low chance of completion
            score += 20
            
        # Determine level
        if score >= 75:
            return {"level": "CRITICAL", "score": score, "color": "red"}
        elif score >= 40:
            return {"level": "HIGH", "score": score, "color": "orange"}
        elif score >= 20:
            return {"level": "MEDIUM", "score": score, "color": "yellow"}
        else:
            return {"level": "LOW", "score": score, "color": "green"}

if __name__ == "__main__":
    model = XGBoostRiskScoringModel()
    dummy_df = pd.DataFrame({"dummy": [1, 2, 3]})
    model.train(dummy_df)
