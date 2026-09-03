"""
Statistical and Distribution Feature Generator for NIRIKSHAK-AI.
Computes log transformations, robust z-scores, IQR outlier flags, and percentile ranks.
Never deletes outliers; signals them for downstream ML engines.
"""

import pandas as pd
import numpy as np

def compute_statistical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes statistical and distribution features on sanctioned_amount and execution duration.
    """
    df = df.copy()

    sanc_amt = pd.to_numeric(df.get("sanctioned_amount", np.nan), errors="coerce")
    days = pd.to_numeric(df.get("sanction_to_completion_days", np.nan), errors="coerce")

    # 1. Log Transformations (safe for non-negative values)
    df["log_sanctioned_amount"] = np.log1p(sanc_amt.clip(lower=0.0).fillna(0.0))
    df["log_execution_days"] = np.log1p(days.clip(lower=0.0).fillna(0.0))

    # 2. Percentile ranks
    valid_sanc = sanc_amt.dropna()
    if len(valid_sanc) > 1:
        df["amount_percentile"] = (sanc_amt.rank(pct=True) * 100.0).round(1)
        mean_amt = valid_sanc.mean()
        std_amt = valid_sanc.std() or 1.0
        df["amount_z_score"] = ((sanc_amt - mean_amt) / std_amt).round(2)

        # IQR-based outlier flag
        q25 = valid_sanc.quantile(0.25)
        q75 = valid_sanc.quantile(0.75)
        iqr = q75 - q25
        upper_bound = q75 + (1.5 * iqr)
        df["amount_iqr_outlier_flag"] = (sanc_amt > upper_bound).astype(int)
    else:
        df["amount_percentile"] = 50.0
        df["amount_z_score"] = 0.0
        df["amount_iqr_outlier_flag"] = 0

    # 3. Execution days statistics
    valid_days = days.dropna()
    if len(valid_days) > 1:
        df["execution_duration_percentile"] = (days.rank(pct=True) * 100.0).round(1)
        mean_d = valid_days.mean()
        std_d = valid_days.std() or 1.0
        df["duration_z_score"] = ((days - mean_d) / std_d).round(2)
        
        # Duration outlier (> 730 days / 2 years or 1.5 * IQR)
        q25_d = valid_days.quantile(0.25)
        q75_d = valid_days.quantile(0.75)
        iqr_d = q75_d - q25_d
        upper_d = q75_d + (1.5 * iqr_d)
        df["duration_iqr_outlier_flag"] = (days > upper_d).astype(int)
    else:
        df["execution_duration_percentile"] = 50.0
        df["duration_z_score"] = 0.0
        df["duration_iqr_outlier_flag"] = 0

    return df

