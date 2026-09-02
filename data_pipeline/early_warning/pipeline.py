import os
import json
import pandas as pd
from data_pipeline.early_warning.alert_generator import generate_early_warning_alerts

def run_early_warning_pipeline():
    print("=========================================================================")
    print("      STARTING EARLY-WARNING ALERT SYSTEM PIPELINE (§14)")
    print("=========================================================================")

    pred_path = os.path.join("data", "predictive", "predictive_risk_scores.csv")
    comp_path = os.path.join("data", "compliance", "compliance_violations.csv")
    ml_path = os.path.join("data", "ml_anomaly", "ml_anomaly_scores.csv")
    stat_path = os.path.join("data", "statistical", "statistical_anomalies.csv")

    df_pred = pd.read_csv(pred_path, low_memory=False) if os.path.exists(pred_path) else pd.DataFrame()
    df_comp = pd.read_csv(comp_path, low_memory=False) if os.path.exists(comp_path) else pd.DataFrame()
    df_ml = pd.read_csv(ml_path, low_memory=False) if os.path.exists(ml_path) else pd.DataFrame()
    df_stat = pd.read_csv(stat_path, low_memory=False) if os.path.exists(stat_path) else pd.DataFrame()

    df_alerts = generate_early_warning_alerts(df_pred, df_comp, df_ml, df_stat)

    ew_dir = os.path.join("data", "early_warning")
    os.makedirs(ew_dir, exist_ok=True)

    # Save top 15,000 highest-priority alerts to keep repository lightweight (<10MB) for GitHub limits
    alerts_csv_path = os.path.join(ew_dir, "alerts.csv")
    df_alerts_tracked = df_alerts.head(15000) if len(df_alerts) > 15000 else df_alerts
    df_alerts_tracked.to_csv(alerts_csv_path, index=False, encoding="utf-8")

    # Generate Early-Warning Summary Report with total dataset metrics
    summary = {
        "status": "SUCCESS",
        "total_works_evaluated": len(df_pred),
        "total_alerts_generated": len(df_alerts),
        "alerts_tracked_in_store": len(df_alerts_tracked),
        "priority_breakdown": df_alerts["priority"].value_counts().to_dict() if not df_alerts.empty else {},
        "status_breakdown": df_alerts["status"].value_counts().to_dict() if not df_alerts.empty else {}
    }

    rep_dir = os.path.join("data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    rep_path = os.path.join(rep_dir, "early_warning_report.json")

    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[NIRIKSHAK AI] Early-Warning Alert Pipeline completed! Generated {len(df_alerts):,} total alerts. Saved top {len(df_alerts_tracked):,} to {alerts_csv_path}")

if __name__ == "__main__":
    run_early_warning_pipeline()
