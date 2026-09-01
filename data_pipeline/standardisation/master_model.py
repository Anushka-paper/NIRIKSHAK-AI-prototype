import os
import numpy as np
import pandas as pd

def build_unified_master_model(df_rec, df_sanc, df_comp, df_exp):
    print("[MASTER MODEL] Building Unified Work-Level Lifecycle Model...")
    
    def safe_sub(df, cols):
        if df.empty:
            return pd.DataFrame()
        avail = [c for c in cols if c in df.columns]
        return df[avail].copy()

    rec_sub = safe_sub(df_rec, ["canonical_work_id", "source_house", "canonical_state", "canonical_constituency", "canonical_mp_name", "canonical_work_category", "work", "recommended_date", "recommended_amount_inr", "canonical_ida"])
    sanc_sub = safe_sub(df_sanc, ["canonical_work_id", "sanction_date", "sanctioned_amount_inr", "canonical_work_status"])
    comp_sub = safe_sub(df_comp, ["canonical_work_id", "completion_date", "completed_disbursed_amount_inr", "image"])
    
    if not df_exp.empty:
        agg_dict = {}
        if "expenditure_amount_inr" in df_exp.columns: agg_dict["expenditure_amount_inr"] = "sum"
        if "canonical_vendor_name" in df_exp.columns: agg_dict["canonical_vendor_name"] = "first"
        if "canonical_payment_status" in df_exp.columns: agg_dict["canonical_payment_status"] = "last"
        if "expenditure_date" in df_exp.columns: agg_dict["expenditure_date"] = "max"
        
        exp_grp = df_exp.groupby("canonical_work_id").agg(agg_dict).reset_index()
    else:
        exp_grp = pd.DataFrame()
    
    # Outer join without column collision
    master = rec_sub
    if not sanc_sub.empty:
        master = master.merge(sanc_sub, on="canonical_work_id", how="outer")
    if not comp_sub.empty:
        master = master.merge(comp_sub, on="canonical_work_id", how="outer")
    if not exp_grp.empty:
        master = master.merge(exp_grp, on="canonical_work_id", how="outer")
    
    # Vectorized lifecycle stage calculation
    comp_date = master["completion_date"] if "completion_date" in master.columns else pd.Series(np.nan, index=master.index)
    exp_amt = master["expenditure_amount_inr"] if "expenditure_amount_inr" in master.columns else pd.Series(np.nan, index=master.index)
    sanc_date = master["sanction_date"] if "sanction_date" in master.columns else pd.Series(np.nan, index=master.index)

    conditions = [
        comp_date.notna(),
        exp_amt.notna() & (exp_amt > 0),
        sanc_date.notna()
    ]
    choices = ["COMPLETED", "IN_PROGRESS", "SANCTIONED"]
    master["lifecycle_stage"] = np.select(conditions, choices, default="RECOMMENDED")
    
    out_dir = os.path.join("data", "standardised", "master")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "unified_work_lifecycle.csv")
    master.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[MASTER MODEL] Saved {len(master):,} unified work records to {out_path}")
    return master
