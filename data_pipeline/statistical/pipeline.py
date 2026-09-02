import os
import json
import pandas as pd
from data_pipeline.statistical.baselines import compute_peer_baselines
from data_pipeline.statistical.anomaly_evaluator import evaluate_statistical_anomalies

def run_statistical_pipeline():
    print("=========================================================================")
    print("      STARTING STATISTICAL & PEER BASELINE ENGINE")
    print("=========================================================================")

    work_feat_path = os.path.join("data", "features", "features_work.csv")
    master_path = os.path.join("data", "integrated", "master", "unified_work_lifecycle.csv")

    df_work = pd.read_csv(work_feat_path, low_memory=False) if os.path.exists(work_feat_path) else pd.DataFrame()
    df_lifecycle = pd.read_csv(master_path, low_memory=False) if os.path.exists(master_path) else pd.DataFrame()

    if not df_lifecycle.empty and "expenditure_amount_inr" in df_lifecycle.columns:
        df_work["expenditure_amount_inr"] = df_lifecycle["expenditure_amount_inr"]

    # Compute Peer Baselines
    df_baselines = compute_peer_baselines(df_work)
    
    # Evaluate Statistical Anomalies
    df_anom = evaluate_statistical_anomalies(df_work, df_baselines)

    stat_dir = os.path.join("data", "statistical")
    os.makedirs(stat_dir, exist_ok=True)

    df_baselines.to_csv(os.path.join(stat_dir, "statistical_baselines.csv"), index=False, encoding="utf-8")
    df_anom.to_csv(os.path.join(stat_dir, "statistical_anomalies.csv"), index=False, encoding="utf-8")

    # Generate Summary Report
    tot_anom = int(df_anom["is_statistical_anom"].sum()) if not df_anom.empty and "is_statistical_anom" in df_anom.columns else 0
    
    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "statistical_report.json")

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "SUCCESS",
            "total_works_evaluated": len(df_work),
            "total_peer_groups": len(df_baselines),
            "total_statistical_anomalies": tot_anom
        }, f, indent=2)

    print(f"[NIRIKSHAK AI] Statistical Engine completed successfully! Report saved to {rep_path}")

if __name__ == "__main__":
    run_statistical_pipeline()
