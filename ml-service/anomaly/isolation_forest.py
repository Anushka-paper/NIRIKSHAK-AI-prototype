"""
Isolation Forest Anomaly Detection Engine for NIRIKSHAK-AI MPLADS Platform.
Implements:
1. Feature extraction from Canonical Feature Store:
   - sanction_amount
   - district_category_median
   - cost_deviation_pct
   - total_expenditure_vs_sanction_amount
   - total_execution_days
   - vendor_txn_count_per_district_per_quarter
   - is_overpayment
   - budget_ceiling_breach_flag
   - evidence_missing_flag
2. Robust scaling and scikit-learn IsolationForest model training.
3. Decision score normalization into [0, 1] anomaly risk score.
4. Explanations per anomalous work (cost inflation, timeline delay, missing evidence, ceiling breach).
5. Persisting model artifacts (.joblib) and prediction records (data/predictions/).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IsolationForestDetector")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FEATURE_DIR = BASE_DIR / "data" / "features"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"

FEATURE_COLUMNS = [
    "sanction_amount",
    "district_category_median",
    "cost_deviation_pct",
    "total_expenditure_vs_sanction_amount",
    "total_execution_days",
    "vendor_txn_count_per_district_per_quarter",
    "is_overpayment",
    "budget_ceiling_breach_flag",
    "evidence_missing_flag"
]

class IsolationForestAnomalyDetector:
    def __init__(
        self,
        n_estimators: int = 200,
        contamination: float = 0.05,
        random_state: int = 42
    ):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.scaler = RobustScaler()
        self.feature_columns = FEATURE_COLUMNS

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepares numerical input matrix from canonical feature store."""
        X = pd.DataFrame(index=df.index)
        for col in self.feature_columns:
            if col in df.columns:
                if df[col].dtype == bool or df[col].dtype == object:
                    X[col] = df[col].astype(bool).astype(float)
                else:
                    X[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            else:
                X[col] = 0.0
        
        # Replace infs and ensure non-negative for amounts
        X = X.replace([np.inf, -np.inf], 0.0).fillna(0.0)
        return X

    def train(self, df: pd.DataFrame, model_path: Optional[Path] = None) -> IsolationForest:
        """Trains Isolation Forest model on canonical feature store."""
        logger.info(f"Training Isolation Forest with n_estimators={self.n_estimators}, contamination={self.contamination} on {len(df)} records...")
        X = self.prepare_features(df)
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.model.fit(X_scaled)

        if model_path:
            model_path.parent.mkdir(parents=True, exist_ok=True)
            bundle = {
                "model": self.model,
                "scaler": self.scaler,
                "feature_columns": self.feature_columns,
                "contamination": self.contamination
            }
            joblib.dump(bundle, model_path)
            logger.info(f"Saved Isolation Forest model bundle to: {model_path}")

        return self.model

    def predict(self, df: pd.DataFrame, model_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Runs inference and computes normalized anomaly score [0, 1] + anomaly flag.
        """
        if self.model is None and model_path and model_path.exists():
            bundle = joblib.load(model_path)
            self.model = bundle["model"]
            self.scaler = bundle["scaler"]
            self.feature_columns = bundle["feature_columns"]

        if self.model is None:
            raise ValueError("Model is not fitted. Call train() or provide a valid model_path.")

        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)

        # Decision function: lower values mean more anomalous
        raw_scores = self.model.decision_function(X_scaled)
        preds = self.model.predict(X_scaled) # -1 = anomaly, 1 = normal

        # Min-max normalize into anomaly risk score in [0.0, 1.0] where 1.0 is highest risk
        min_s = raw_scores.min()
        max_s = raw_scores.max()
        denom = (max_s - min_s) if (max_s - min_s) > 0 else 1.0
        anomaly_scores = np.clip(1.0 - ((raw_scores - min_s) / denom), 0.0, 1.0)
        anomaly_flags = (preds == -1)

        result_df = df.copy()
        result_df["anomaly_score"] = np.round(anomaly_scores, 4)
        result_df["is_anomaly"] = anomaly_flags
        result_df["raw_decision_score"] = np.round(raw_scores, 4)

        # Generate rule-informed explanation tags for anomalies
        explanations = []
        for idx, row in result_df.iterrows():
            reasons = []
            if row.get("cost_deviation_pct", 0.0) > 100.0:
                reasons.append(f"Sanction cost {row.get('cost_deviation_pct'):.1f}% above district-category median")
            if row.get("is_overpayment", False) or row.get("total_expenditure_vs_sanction_amount", 0.0) > 1.05:
                reasons.append("Tranche disbursement exceeded sanctioned allocation")
            if row.get("budget_ceiling_breach_flag", False):
                reasons.append("MP recommended allocation breached sanctioned ceiling")
            if row.get("evidence_missing_flag", False):
                reasons.append("Physical completion recorded without photo evidence")
            if row.get("total_execution_days", 0) > 730:
                reasons.append(f"Excessive execution duration ({int(row.get('total_execution_days'))} days)")
            if row.get("vendor_txn_count_per_district_per_quarter", 0) > 15:
                reasons.append("High quarterly vendor concentration density")
            
            if not reasons and row["is_anomaly"]:
                reasons.append("Multivariate outlier across financial & timeline features")
            explanations.append(" | ".join(reasons) if reasons else "Normal Pattern")

        result_df["anomaly_reasons"] = explanations
        return result_df

def run_isolation_forest_pipeline(parliament: str = "all") -> Dict[str, Any]:
    """
    Executes end-to-end Isolation Forest training and inference on Canonical Feature Stores.
    Outputs:
    - artifacts/isolation_forest_{parliament}.joblib
    - data/predictions/{parliament}/work_anomalies.csv
    - data/predictions/{parliament}/anomaly_summary.json
    """
    parliaments = ["lok_sabha", "rajya_sabha"] if parliament == "all" else [parliament]
    overall_summary = {}

    for house in parliaments:
        feat_path = FEATURE_DIR / house / "canonical_work_features.csv"
        if not feat_path.exists():
            logger.warning(f"Canonical feature store not found at {feat_path}. Skipping {house}.")
            continue

        logger.info(f"\n=======================================================")
        logger.info(f"RUNNING ISOLATION FOREST ANOMALY DETECTION FOR {house.upper()}")
        logger.info(f"=======================================================")

        df_features = pd.read_csv(feat_path, low_memory=False)
        logger.info(f"Loaded {len(df_features)} works from {feat_path.name}")

        detector = IsolationForestAnomalyDetector(n_estimators=250, contamination=0.05, random_state=42)
        model_file = ARTIFACTS_DIR / f"isolation_forest_{house}.joblib"
        detector.train(df_features, model_path=model_file)

        # Run inference
        pred_df = detector.predict(df_features, model_path=model_file)

        # Persist predictions
        out_house_dir = PREDICTIONS_DIR / house
        out_house_dir.mkdir(parents=True, exist_ok=True)
        pred_csv = out_house_dir / "work_anomalies.csv"
        
        # Select output columns
        export_cols = [
            "work_id", "category", "description", "mp_id", "constituency_id", "state", "parliament",
            "sanction_amount", "district_category_median", "cost_deviation_pct",
            "total_expenditure", "total_execution_days", "has_evidence",
            "anomaly_score", "is_anomaly", "anomaly_reasons"
        ]
        available_export = [c for c in export_cols if c in pred_df.columns]
        pred_df[available_export].to_csv(pred_csv, index=False)

        # Compute summary metrics
        total_works = len(pred_df)
        anomaly_count = int(pred_df["is_anomaly"].sum())
        anomaly_rate = round((anomaly_count / total_works) * 100.0, 2)
        high_risk_count = int((pred_df["anomaly_score"] >= 0.75).sum())

        house_summary = {
            "parliament": house,
            "total_works_evaluated": total_works,
            "anomalies_detected": anomaly_count,
            "anomaly_rate_pct": anomaly_rate,
            "high_risk_works_count": high_risk_count,
            "features_utilized": FEATURE_COLUMNS,
            "model_path": str(model_file),
            "predictions_path": str(pred_csv)
        }

        summary_json = out_house_dir / "anomaly_summary.json"
        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump(house_summary, f, indent=2)

        logger.info(f"[{house.upper()}] Identified {anomaly_count:,} anomalies ({anomaly_rate}%) out of {total_works:,} works.")
        logger.info(f"Predictions saved -> {pred_csv}")
        logger.info(f"Summary saved -> {summary_json}")
        overall_summary[house] = house_summary

    return overall_summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Isolation Forest Anomaly Detection")
    parser.add_argument("--parliament", "-p", default="all", choices=["lok_sabha", "rajya_sabha", "all"])
    args = parser.parse_args()
    run_isolation_forest_pipeline(parliament=args.parliament)
