import pandas as pd
import numpy as np
import os
import joblib

class DelayPredictionModel:
    def __init__(self):
        self.model = None

    def train(self, data: pd.DataFrame):
        # We simulate the CoxPH training because lifelines might not be installed
        # and we don't have time-to-event data in our simulated loksabha_expenditure yet.
        print("Training Delay Prediction Model (CoxPH Simulation)...")
        # In a real scenario, this would use lifelines.CoxPHFitter
        self.model = "cox_ph_model_trained"
        
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        joblib.dump(self, os.path.join(models_dir, 'delay_prediction_model.joblib'))
        print("Delay Prediction Model saved.")

    def predict_survival(self, features: dict):
        # Simulates the probability of completing a project within given days
        # E.g. {"sanctioned_amount": 5000000, "work_category": "Roads"}
        
        # Simulated risk based on amount
        amt = features.get("sanctioned_amount", 100000)
        base_risk = min(amt / 10000000, 0.5) # higher amount -> slightly higher risk of delay
        
        # Return probability of completion by day 30, 90, 365
        return {
            "day_30": round(max(0.0, 0.2 - base_risk), 2),
            "day_90": round(max(0.0, 0.6 - base_risk), 2),
            "day_365": round(max(0.0, 0.95 - (base_risk/2)), 2)
        }

if __name__ == "__main__":
    model = DelayPredictionModel()
    dummy_df = pd.DataFrame({"dummy": [1, 2, 3]})
    model.train(dummy_df)
