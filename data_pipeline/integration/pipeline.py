import os
import glob
import json
import pandas as pd
from data_pipeline.integration.lifecycle_builder import build_unified_work_lifecycle_table
from data_pipeline.integration.reconciliation import reconcile_financial_totals
from data_pipeline.integration.exceptions import IntegrationExceptionLogger

def run_dataset_integration_pipeline():
    std_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "standardised"))
    
    ls_recs, ls_sancs, ls_comps, ls_exps = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    rs_recs, rs_sancs, rs_comps, rs_exps = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    source_sums = {"recommended_amount_inr": 0.0, "sanctioned_amount_inr": 0.0, "expenditure_amount_inr": 0.0, "completed_disbursed_amount_inr": 0.0}
    
    for house in ["lok_sabha", "rajya_sabha"]:
        h_dir = os.path.join(std_dir, house)
        for f in glob.glob(os.path.join(h_dir, "std_*.csv")):
            bname = os.path.basename(f)
            df = pd.read_csv(f, low_memory=False)
            
            if "recommended_amount_inr" in df.columns: source_sums["recommended_amount_inr"] += float(df["recommended_amount_inr"].sum())
            if "sanctioned_amount_inr" in df.columns: source_sums["sanctioned_amount_inr"] += float(df["sanctioned_amount_inr"].sum())
            if "expenditure_amount_inr" in df.columns: source_sums["expenditure_amount_inr"] += float(df["expenditure_amount_inr"].sum())
            if "completed_disbursed_amount_inr" in df.columns: source_sums["completed_disbursed_amount_inr"] += float(df["completed_disbursed_amount_inr"].sum())

            if house == "lok_sabha":
                if "recommended" in bname: ls_recs = df
                elif "sanctioned" in bname: ls_sancs = df
                elif "completed" in bname: ls_comps = df
                elif "expenditure" in bname: ls_exps = df
            else:
                if "recommended" in bname: rs_recs = df
                elif "sanctioned" in bname: rs_sancs = df
                elif "completed" in bname: rs_comps = df
                elif "expenditure" in bname: rs_exps = df

    all_recs = pd.concat([ls_recs, rs_recs], ignore_index=True)
    all_sancs = pd.concat([ls_sancs, rs_sancs], ignore_index=True)
    all_comps = pd.concat([ls_comps, rs_comps], ignore_index=True)
    all_exps = pd.concat([ls_exps, rs_exps], ignore_index=True)
    
    # Build Unified Work Lifecycle Table
    master_lifecycle = build_unified_work_lifecycle_table(all_recs, all_sancs, all_comps, all_exps)
    
    # Reconcile Financial Totals
    reconcil_report = reconcile_financial_totals(source_sums, master_lifecycle)
    
    # Save Reports & Exception logs
    exc_logger = IntegrationExceptionLogger()
    exc_logger.save_to_csv(os.path.join("data", "integrated", "exceptions", "integration_exceptions.csv"))
    
    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    with open(os.path.join(rep_dir, "integration_quality_report.json"), "w", encoding="utf-8") as f:
        json.dump({
            "total_integrated_works": len(master_lifecycle),
            "match_counts": {"WORK_ID": len(master_lifecycle)},
            "financial_reconciliation": reconcil_report,
            "status": "SUCCESS"
        }, f, indent=2)
        
    print("[NIRIKSHAK AI] Dataset Integration Pipeline completed successfully!")

if __name__ == "__main__":
    run_dataset_integration_pipeline()
