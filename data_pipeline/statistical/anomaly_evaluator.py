import numpy as np
import pandas as pd
from data_pipeline.statistical.config import ZSCORE_THRESHOLD
from data_pipeline.statistical.peer_grouper import assign_peer_groups

def evaluate_statistical_anomalies(df_work, df_baselines):
    if df_work.empty or df_baselines.empty:
        return pd.DataFrame()
        
    print(f"[STATISTICAL ENGINE] Evaluating statistical anomalies for {len(df_work):,} works...")
    df = assign_peer_groups(df_work)
    
    merged = df.merge(df_baselines, on="peer_group_key", how="left")
    
    # Calculate Z-Scores
    exp_amt = pd.to_numeric(merged.get("expenditure_amount_inr", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)
    exp_mean = merged["exp_mean"].fillna(0.0)
    exp_std = merged["exp_std"].replace(0, np.nan).fillna(1.0)
    
    merged["amount_zscore"] = (exp_amt - exp_mean) / exp_std
    
    sanc_delay = pd.to_numeric(merged.get("sanction_delay_days", pd.Series(np.nan, index=merged.index)), errors="coerce")
    delay_mean = merged["delay_mean"].fillna(0.0)
    delay_std = merged["delay_std"].replace(0, np.nan).fillna(1.0)
    
    merged["delay_zscore"] = (sanc_delay - delay_mean) / delay_std
    
    # Outlier Flags
    merged["iqr_amount_outlier"] = exp_amt > merged["exp_upper_fence"]
    merged["iqr_delay_outlier"] = sanc_delay > merged["delay_upper_fence"]
    merged["zscore_outlier"] = (merged["amount_zscore"].abs() > ZSCORE_THRESHOLD) | (merged["delay_zscore"].abs() > ZSCORE_THRESHOLD)

    # 0 to 100 Normalized Statistical Anomaly Score
    abs_z = np.maximum(merged["amount_zscore"].abs().fillna(0.0), merged["delay_zscore"].abs().fillna(0.0))
    merged["statistical_anomaly_score"] = np.minimum(100.0, np.round((abs_z / 4.0) * 100.0, 1))

    merged["is_statistical_anom"] = merged["iqr_amount_outlier"] | merged["iqr_delay_outlier"] | merged["zscore_outlier"]

    keep_cols = [
        "canonical_work_id", "peer_group_key", "project_size_tier", "expenditure_amount_inr",
        "sanction_delay_days", "amount_zscore", "delay_zscore", "iqr_amount_outlier",
        "iqr_delay_outlier", "zscore_outlier", "statistical_anomaly_score", "is_statistical_anom"
    ]
    res_cols = [c for c in keep_cols if c in merged.columns]
    return merged[res_cols]
