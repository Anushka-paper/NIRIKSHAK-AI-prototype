import numpy as np
import pandas as pd
from data_pipeline.features.config import FEATURE_VERSION
from data_pipeline.features.incremental import compute_row_hash

def compute_transaction_features(df_exp, df_lifecycle):
    if df_exp.empty:
        return pd.DataFrame()
    print(f"[FEATURE STORE] Computing features_transaction for {len(df_exp):,} records...")
    
    df = df_exp.copy()
    if "transaction_id" not in df.columns:
        df["transaction_id"] = [f"TXN_{i+1:08d}" for i in range(len(df))]
        
    cols_to_fetch = ["canonical_work_id", "sanctioned_amount_inr", "sanction_date", "completion_date", "canonical_work_category"]
    avail_cols = [c for c in cols_to_fetch if c in df_lifecycle.columns] if not df_lifecycle.empty else []
    
    life_sub = df_lifecycle[avail_cols].drop_duplicates("canonical_work_id") if avail_cols else pd.DataFrame()
    if not life_sub.empty:
        df = df.merge(life_sub, on="canonical_work_id", how="left")
        
    amt = pd.to_numeric(df.get("expenditure_amount_inr", pd.Series(np.nan, index=df.index)), errors="coerce")
    cat = df.get("canonical_work_category", pd.Series("OTHER_WORKS", index=df.index)).fillna("OTHER_WORKS")
    
    # Amount Z-score & Percentile per Category
    cat_mean = df.groupby(cat)["expenditure_amount_inr"].transform("mean")
    cat_std = df.groupby(cat)["expenditure_amount_inr"].transform("std").replace(0, np.nan)
    df["amount_zscore"] = (amt - cat_mean) / cat_std
    df["amount_percentile"] = df.groupby(cat)["expenditure_amount_inr"].transform(lambda x: x.rank(pct=True) * 100.0 if len(x.dropna()) > 0 else np.nan)

    # Expenditure to Sanction %
    sanc_amt = pd.to_numeric(df.get("sanctioned_amount_inr", pd.Series(np.nan, index=df.index)), errors="coerce")
    df["expenditure_to_sanction_pct"] = np.where((sanc_amt > 0) & (amt.notna()), (amt / sanc_amt) * 100.0, np.nan)
    
    # Round Amount Flag
    df["is_round_amount"] = (amt > 0) & ((amt % 10000 == 0) | (amt % 100000 == 0))
    
    # Date Calculations
    exp_dt = pd.to_datetime(df.get("expenditure_date", pd.Series(pd.NaT, index=df.index)), errors="coerce")
    sanc_dt = pd.to_datetime(df.get("sanction_date", pd.Series(pd.NaT, index=df.index)), errors="coerce")
    comp_dt = pd.to_datetime(df.get("completion_date", pd.Series(pd.NaT, index=df.index)), errors="coerce")
    
    df["days_since_sanction"] = (exp_dt - sanc_dt).dt.days.astype(float)
    df["days_to_completion"] = (comp_dt - exp_dt).dt.days.astype(float)
    
    df["feature_version"] = FEATURE_VERSION
    df["computed_at"] = pd.Timestamp.now().isoformat()
    df["row_hash"] = df["transaction_id"].apply(lambda x: compute_row_hash(str(x)))

    keep_cols = [
        "transaction_id", "canonical_work_id", "canonical_vendor_name", "expenditure_amount_inr",
        "amount_zscore", "amount_percentile", "expenditure_to_sanction_pct", "is_round_amount",
        "days_since_sanction", "days_to_completion", "feature_version", "computed_at", "row_hash"
    ]
    res_cols = [c for c in keep_cols if c in df.columns]
    return df[res_cols]
