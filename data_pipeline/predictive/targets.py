import numpy as np
import pandas as pd
from data_pipeline.predictive.config import DELAY_SANCTION_THRESHOLD, DELAY_COMPLETION_THRESHOLD, STAGNATION_AGE_THRESHOLD

def generate_target_labels(df_work, df_lifecycle):
    df = df_work.copy()
    
    if not df_lifecycle.empty and "expenditure_amount_inr" in df_lifecycle.columns:
        df["expenditure_amount_inr"] = df_lifecycle["expenditure_amount_inr"]
        df["sanctioned_amount_inr"] = df_lifecycle.get("sanctioned_amount_inr", 0.0)
        df["recommended_amount_inr"] = df_lifecycle.get("recommended_amount_inr", 0.0)

    # 1. is_delayed
    sanc_delay = pd.to_numeric(df.get("sanction_delay_days", pd.Series(np.nan, index=df.index)), errors="coerce").fillna(0.0)
    comp_delay = pd.to_numeric(df.get("completion_delay_days", pd.Series(np.nan, index=df.index)), errors="coerce").fillna(0.0)
    
    df["is_delayed"] = ((sanc_delay > DELAY_SANCTION_THRESHOLD) | (comp_delay > DELAY_COMPLETION_THRESHOLD)).astype(int)
    
    # 2. expected_delay_days
    df["expected_delay_days"] = np.maximum(0.0, sanc_delay) + np.maximum(0.0, comp_delay)

    # 3. is_cost_overrun
    sanc_amt = pd.to_numeric(df.get("sanctioned_amount_inr", pd.Series(0.0, index=df.index)), errors="coerce").fillna(0.0)
    exp_amt = pd.to_numeric(df.get("expenditure_amount_inr", pd.Series(0.0, index=df.index)), errors="coerce").fillna(0.0)
    overrun = pd.to_numeric(df.get("overrun_pct", pd.Series(0.0, index=df.index)), errors="coerce").fillna(0.0)
    
    df["is_cost_overrun"] = (((sanc_amt > 0) & (exp_amt > sanc_amt)) | (overrun > 0)).astype(int)

    # 4. is_stagnant
    has_sanc = df.get("has_sanction", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    has_exp = df.get("has_expenditure", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    inact_days = pd.to_numeric(df.get("inactivity_gap_days", pd.Series(0.0, index=df.index)), errors="coerce").fillna(0.0)
    
    df["is_stagnant"] = (has_sanc & (~has_exp) & (inact_days >= STAGNATION_AGE_THRESHOLD)).astype(int)

    return df
