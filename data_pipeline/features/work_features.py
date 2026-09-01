import numpy as np
import pandas as pd
from data_pipeline.features.config import FEATURE_VERSION
from data_pipeline.features.incremental import compute_row_hash

def compute_work_features(df_lifecycle):
    print(f"[FEATURE STORE] Computing features_work for {len(df_lifecycle):,} records...")
    df = df_lifecycle.copy()
    
    rec_dt = pd.to_datetime(df["recommended_date"], errors="coerce") if "recommended_date" in df.columns else pd.Series(pd.NaT, index=df.index)
    sanc_dt = pd.to_datetime(df["sanction_date"], errors="coerce") if "sanction_date" in df.columns else pd.Series(pd.NaT, index=df.index)
    comp_dt = pd.to_datetime(df["completion_date"], errors="coerce") if "completion_date" in df.columns else pd.Series(pd.NaT, index=df.index)
    exp_dt = pd.to_datetime(df["expenditure_date"], errors="coerce") if "expenditure_date" in df.columns else pd.Series(pd.NaT, index=df.index)

    # Delays
    df["sanction_delay_days"] = (sanc_dt - rec_dt).dt.days.astype(float)
    df["completion_delay_days"] = (comp_dt - sanc_dt).dt.days.astype(float)
    
    ref_now = pd.to_datetime("today")
    latest_dt = comp_dt.fillna(exp_dt).fillna(sanc_dt)
    df["inactivity_gap_days"] = (ref_now - latest_dt).dt.days.astype(float)

    # Duration Percentile
    df["duration_days"] = (comp_dt - sanc_dt).dt.days
    df["duration_percentile"] = df.groupby("canonical_work_category")["duration_days"].transform(lambda x: x.rank(pct=True) * 100.0 if len(x.dropna()) > 0 else np.nan)

    # Variances & Overruns
    rec_amt = pd.to_numeric(df.get("recommended_amount_inr", pd.Series(np.nan, index=df.index)), errors="coerce")
    sanc_amt = pd.to_numeric(df.get("sanctioned_amount_inr", pd.Series(np.nan, index=df.index)), errors="coerce")
    exp_amt = pd.to_numeric(df.get("expenditure_amount_inr", pd.Series(np.nan, index=df.index)), errors="coerce")

    df["estimate_variance_pct"] = np.where((rec_amt > 0) & (sanc_amt.notna()), ((sanc_amt - rec_amt) / rec_amt) * 100.0, np.nan)
    df["overrun_pct"] = np.where((sanc_amt > 0) & (exp_amt.notna()), ((exp_amt - sanc_amt) / sanc_amt) * 100.0, np.nan)

    # Text Features
    work_text = df["work"].astype(str).fillna("") if "work" in df.columns else pd.Series("", index=df.index)
    df["text_length_char"] = work_text.str.len()
    df["text_word_count"] = work_text.str.split().str.len()

    # Metadata & Versioning
    df["feature_version"] = FEATURE_VERSION
    df["computed_at"] = pd.Timestamp.now().isoformat()
    df["row_hash"] = df["canonical_work_id"].apply(lambda x: compute_row_hash(str(x)))

    keep_cols = [
        "canonical_work_id", "source_house", "canonical_state", "canonical_constituency", "canonical_mp_name", "canonical_work_category",
        "sanction_delay_days", "completion_delay_days", "inactivity_gap_days", "duration_percentile",
        "estimate_variance_pct", "overrun_pct", "has_recommendation", "has_sanction", "has_expenditure", "has_completion",
        "lifecycle_completeness_ratio", "lifecycle_stage", "text_length_char", "text_word_count", "feature_version", "computed_at", "row_hash"
    ]
    res_cols = [c for c in keep_cols if c in df.columns]
    return df[res_cols]
