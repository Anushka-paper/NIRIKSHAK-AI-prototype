import pandas as pd

def pre_aggregate_expenditure(df_exp):
    if df_exp.empty or "canonical_work_id" not in df_exp.columns:
        return pd.DataFrame()
        
    print(f"[INTEGRATION GUARD] Pre-aggregating {len(df_exp):,} transaction expenditure records...")
    
    agg_rules = {}
    if "expenditure_amount_inr" in df_exp.columns:
        agg_rules["expenditure_amount_inr"] = "sum"
    if "canonical_vendor_name" in df_exp.columns:
        agg_rules["canonical_vendor_name"] = "first"
    if "canonical_payment_status" in df_exp.columns:
        agg_rules["canonical_payment_status"] = "last"
    if "expenditure_date" in df_exp.columns:
        agg_rules["expenditure_date"] = "max"
        
    exp_grp = df_exp.groupby("canonical_work_id").agg(agg_rules).reset_index()
    exp_grp["expenditure_transaction_count"] = df_exp.groupby("canonical_work_id").size().values
    
    print(f"[INTEGRATION GUARD] Aggregated into {len(exp_grp):,} unique work expenditure records (0 row multiplication).")
    return exp_grp
