import os
import json
import pandas as pd
from data_pipeline.compliance.evaluator import ComplianceEvaluator

def run_compliance_pipeline():
    print("=========================================================================")
    print("      STARTING DETERMINISTIC COMPLIANCE RULE ENGINE")
    print("=========================================================================")

    work_feat_path = os.path.join("data", "features", "features_work.csv")
    txn_feat_path = os.path.join("data", "features", "features_transaction.csv")
    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")

    df_work = pd.read_csv(work_feat_path, low_memory=False) if os.path.exists(work_feat_path) else pd.DataFrame()
    df_txn = pd.read_csv(txn_feat_path, low_memory=False) if os.path.exists(txn_feat_path) else pd.DataFrame()
    df_lifecycle = pd.read_csv(master_path, low_memory=False) if os.path.exists(master_path) else pd.DataFrame()

    evaluator = ComplianceEvaluator()
    df_viol = evaluator.run_all_evaluations(df_work, df_lifecycle, df_txn)

    comp_dir = os.path.join("data", "compliance")
    os.makedirs(comp_dir, exist_ok=True)

    viol_csv_path = os.path.join(comp_dir, "compliance_violations.csv")
    df_viol.to_csv(viol_csv_path, index=False, encoding="utf-8")

    # Generate Compliance Summary
    summary_data = []
    if not df_viol.empty:
        sev_counts = df_viol["severity"].value_counts().to_dict()
        rule_counts = df_viol["rule_code"].value_counts().to_dict()
    else:
        sev_counts, rule_counts = {}, {}

    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "compliance_report.json")

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "SUCCESS",
            "total_works_evaluated": len(df_work),
            "total_violations": len(df_viol),
            "severity_breakdown": sev_counts,
            "rule_breakdown": rule_counts
        }, f, indent=2)

    print(f"[NIRIKSHAK AI] Compliance Rule Engine completed successfully! Report saved to {rep_path}")

if __name__ == "__main__":
    run_compliance_pipeline()
