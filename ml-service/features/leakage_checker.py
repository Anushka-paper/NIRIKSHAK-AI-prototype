"""
Feature Leakage Checker and Target Separation for NIRIKSHAK-AI.
Categorizes features relative to prediction milestones (e.g. Sanction Date)
and generates feature_leakage_report.csv.
"""

from typing import List, Dict, Any
import pandas as pd
from .config import POST_SANCTION_LEAKAGE_COLUMNS

def check_feature_leakage(columns: List[str], prediction_milestone: str = "sanction_date") -> pd.DataFrame:
    """
    Evaluates every column in the feature dataset against the prediction milestone.
    Classifies as:
      - AVAILABLE_AT_PREDICTION (Safe for pre-sanction predictive models)
      - POST_PREDICTION (Contains post-sanction outcomes; strictly for analytics, anomaly detection, or evaluation)
      - METADATA / IDENTIFIER
    """
    records = []
    
    for col in columns:
        col_lower = col.lower()
        if col in ["canonical_work_id", "official_work_id", "parliament", "state", "constituency", "mp_name"]:
            status = "IDENTIFIER"
            reason = "Entity identification and dimensional routing"
        elif "historical" in col_lower:
            status = "AVAILABLE_AT_PREDICTION"
            reason = "Time-aware historical metric strictly computed using prior works. Safe for pre-sanction predictive models."
        elif col in POST_SANCTION_LEAKAGE_COLUMNS or any(post in col_lower for post in ["completion", "last_expenditure", "unspent", "target"]):
            status = "POST_PREDICTION"
            reason = "Reflects post-sanction or final lifecycle milestone. Exclude from pre-execution prediction feature matrices."
        else:
            status = "AVAILABLE_AT_PREDICTION"
            reason = "Available at or prior to sanction decision timestamp. Safe for delay/cost risk prediction."

        records.append({
            "feature_name": col,
            "prediction_milestone": prediction_milestone,
            "leakage_status": status,
            "rationale": reason
        })

    return pd.DataFrame(records)
