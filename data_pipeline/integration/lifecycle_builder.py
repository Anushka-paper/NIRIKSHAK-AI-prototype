import os
import numpy as np
import pandas as pd
from data_pipeline.integration.multiplication_guard import pre_aggregate_expenditure

def build_unified_work_lifecycle_table(df_rec, df_sanc, df_comp, df_exp):
    print("[LIFECYCLE BUILDER] Constructing unified work lifecycle table...")
    
    def safe_sub(df, cols):
        if df.empty:
            return pd.DataFrame()
        avail = [c for c in cols if c in df.columns]
        return df[avail].copy()

    rec_sub = safe_sub(df_rec, ["canonical_work_id", "source_house", "canonical_state", "canonical_constituency", "canonical_mp_name", "canonical_work_category", "work", "recommended_date", "recommended_amount_inr", "canonical_ida"])
    sanc_sub = safe_sub(df_sanc, ["canonical_work_id", "sanction_date", "sanctioned_amount_inr", "canonical_work_status"])
    comp_sub = safe_sub(df_comp, ["canonical_work_id", "completion_date", "completed_disbursed_amount_inr", "image"])
    
    exp_agg = pre_aggregate_expenditure(df_exp)
    
    # Outer join work datasets
    master = rec_sub
    if not sanc_sub.empty:
        master = master.merge(sanc_sub, on="canonical_work_id", how="outer")
    if not comp_sub.empty:
        master = master.merge(comp_sub, on="canonical_work_id", how="outer")
    if not exp_agg.empty:
        master = master.merge(exp_agg, on="canonical_work_id", how="outer")
        
    # Generate lifecycle stage indicators
    rec_date = master["recommended_date"] if "recommended_date" in master.columns else pd.Series(np.nan, index=master.index)
    sanc_date = master["sanction_date"] if "sanction_date" in master.columns else pd.Series(np.nan, index=master.index)
    exp_amt = master["expenditure_amount_inr"] if "expenditure_amount_inr" in master.columns else pd.Series(np.nan, index=master.index)
    comp_date = master["completion_date"] if "completion_date" in master.columns else pd.Series(np.nan, index=master.index)

    master["has_recommendation"] = rec_date.notna()
    master["has_sanction"] = sanc_date.notna()
    master["has_expenditure"] = exp_amt.notna() & (exp_amt > 0)
    master["has_completion"] = comp_date.notna()
    
    # Completeness Ratio (0.25 to 1.0)
    stage_sum = master["has_recommendation"].astype(int) + master["has_sanction"].astype(int) + master["has_expenditure"].astype(int) + master["has_completion"].astype(int)
    master["lifecycle_completeness_ratio"] = round(stage_sum / 4.0, 2)

    conditions = [
        comp_date.notna(),
        exp_amt.notna() & (exp_amt > 0),
        sanc_date.notna()
    ]
    choices = ["COMPLETED", "IN_PROGRESS", "SANCTIONED"]
    master["lifecycle_stage"] = np.select(conditions, choices, default="RECOMMENDED")
    master["match_method"] = "WORK_ID"
    master["match_confidence"] = "HIGH"

    out_dir = os.path.join("data", "integrated", "master")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "unified_work_lifecycle.csv")
    master.to_csv(out_path, index=False, encoding="utf-8")
    
    print(f"[LIFECYCLE BUILDER] Unified work lifecycle table saved with {len(master):,} records to {out_path}")
    return master
