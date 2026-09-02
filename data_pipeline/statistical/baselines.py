import numpy as np
import pandas as pd
from data_pipeline.statistical.config import IQR_MULTIPLIER
from data_pipeline.statistical.peer_grouper import assign_peer_groups

def compute_peer_baselines(df_work):
    if df_work.empty:
        return pd.DataFrame()
        
    df = assign_peer_groups(df_work)
    print(f"[STATISTICAL ENGINE] Computing peer baselines across {df['peer_group_key'].nunique():,} unique peer groups...")
    
    baselines = []
    
    for key, group in df.groupby("peer_group_key"):
        cat, state, tier = key.split("::")
        n_works = len(group)
        
        # Expenditure Stats
        exp_amt = pd.to_numeric(group.get("expenditure_amount_inr", pd.Series(np.nan, index=group.index)), errors="coerce").dropna()
        exp_mean = float(exp_amt.mean()) if len(exp_amt) > 0 else 0.0
        exp_std = float(exp_amt.std()) if len(exp_amt) > 1 else 0.0
        exp_q1 = float(exp_amt.quantile(0.25)) if len(exp_amt) > 0 else 0.0
        exp_q3 = float(exp_amt.quantile(0.75)) if len(exp_amt) > 0 else 0.0
        exp_iqr = exp_q3 - exp_q1
        exp_upper = exp_q3 + (IQR_MULTIPLIER * exp_iqr)
        exp_lower = max(0.0, exp_q1 - (IQR_MULTIPLIER * exp_iqr))

        # Delay Stats
        delay = pd.to_numeric(group.get("sanction_delay_days", pd.Series(np.nan, index=group.index)), errors="coerce").dropna()
        delay_mean = float(delay.mean()) if len(delay) > 0 else 0.0
        delay_std = float(delay.std()) if len(delay) > 1 else 0.0
        delay_q1 = float(delay.quantile(0.25)) if len(delay) > 0 else 0.0
        delay_q3 = float(delay.quantile(0.75)) if len(delay) > 0 else 0.0
        delay_iqr = delay_q3 - delay_q1
        delay_upper = delay_q3 + (IQR_MULTIPLIER * delay_iqr)

        baselines.append({
            "peer_group_key": key,
            "category": cat,
            "state": state,
            "size_tier": tier,
            "peer_count": n_works,
            "exp_mean": round(exp_mean, 2),
            "exp_std": round(exp_std, 2),
            "exp_q1": round(exp_q1, 2),
            "exp_q3": round(exp_q3, 2),
            "exp_iqr": round(exp_iqr, 2),
            "exp_upper_fence": round(exp_upper, 2),
            "exp_lower_fence": round(exp_lower, 2),
            "delay_mean": round(delay_mean, 2),
            "delay_std": round(delay_std, 2),
            "delay_upper_fence": round(delay_upper, 2)
        })

    df_base = pd.DataFrame(baselines)
    return df_base
