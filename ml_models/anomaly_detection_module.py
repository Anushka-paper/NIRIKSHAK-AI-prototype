import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import joblib
import os

class AnomalyDetector:
    def __init__(self):
        self.if_model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.lof_model = LocalOutlierFactor(n_neighbors=20, contamination=0.05, novelty=True)

    def train(self, df: pd.DataFrame, features: list):
        """Train both anomaly detection models"""
        X = df[features].fillna(0)
        print("Training Isolation Forest...")
        self.if_model.fit(X)
        print("Training Local Outlier Factor...")
        self.lof_model.fit(X)

    def predict(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """Predict anomalies and assign risk levels"""
        X = df[features].fillna(0)
        
        # 1 for inliers, -1 for outliers
        if_preds = self.if_model.predict(X)
        lof_preds = self.lof_model.predict(X)
        
        df['if_anomaly'] = np.where(if_preds == -1, True, False)
        df['lof_anomaly'] = np.where(lof_preds == -1, True, False)
        
        # Calculate a combined risk score based on both models
        df['risk_score'] = (df['if_anomaly'].astype(int) + df['lof_anomaly'].astype(int))
        
        def assign_risk_level(score):
            if score == 2: return 'Critical'
            if score == 1: return 'High'
            return 'Low'
            
        df['risk_level'] = df['risk_score'].apply(assign_risk_level)
        return df

    def save(self, filepath_prefix: str):
        """Save models using joblib"""
        os.makedirs(os.path.dirname(filepath_prefix), exist_ok=True)
        joblib.dump(self.if_model, f"{filepath_prefix}_if.joblib")
        joblib.dump(self.lof_model, f"{filepath_prefix}_lof.joblib")
        print(f"Models saved to {filepath_prefix}_*.joblib")

    @classmethod
    def load(cls, filepath_prefix: str):
        """Load models using joblib"""
        instance = cls()
        instance.if_model = joblib.load(f"{filepath_prefix}_if.joblib")
        instance.lof_model = joblib.load(f"{filepath_prefix}_lof.joblib")
        return instance
