import json
import pandas as pd
from datetime import datetime
from data_pipeline.early_warning.config import ALERT_PRIORITY_THRESHOLDS, DEFAULT_EVIDENCE_TEMPLATE

def generate_early_warning_alerts(df_predictive, df_compliance, df_ml_anomaly, df_stat_anomaly):
    """
    Synthesizes risk signals across all analytical layers and generates structured Alert Objects with Evidence Packages (§14).
    """
    alerts = []
    if df_predictive.empty:
        return pd.DataFrame()

    # Index compliance violations by entity_id
    comp_map = {}
    if not df_compliance.empty and "entity_id" in df_compliance.columns:
        for r in df_compliance.to_dict(orient="records"):
            eid = str(r["entity_id"]).strip()
            if eid not in comp_map:
                comp_map[eid] = []
            comp_map[eid].append(r)

    # Index ML anomaly scores by canonical_work_id
    ml_map = {}
    if not df_ml_anomaly.empty and "canonical_work_id" in df_ml_anomaly.columns:
        for r in df_ml_anomaly.to_dict(orient="records"):
            ml_map[str(r["canonical_work_id"]).strip()] = r

    # Index statistical anomalies by canonical_work_id
    stat_map = {}
    if not df_stat_anomaly.empty and "canonical_work_id" in df_stat_anomaly.columns:
        for r in df_stat_anomaly.to_dict(orient="records"):
            stat_map[str(r["canonical_work_id"]).strip()] = r

    for work in df_predictive.to_dict(orient="records"):
        wid = str(work.get("canonical_work_id", "")).strip()
        risk_score = float(work.get("project_risk_score", 0.0) or 0.0)

        # Trigger threshold crossing alert if risk_score >= 25.0 or compliance violations exist
        c_flags = comp_map.get(wid, [])
        m_flag = ml_map.get(wid, None)
        s_flag = stat_map.get(wid, None)

        if risk_score < ALERT_PRIORITY_THRESHOLDS["MEDIUM"] and not c_flags and not m_flag:
            continue

        # Determine alert priority
        if risk_score >= ALERT_PRIORITY_THRESHOLDS["CRITICAL"] or any(c["severity"] == "CRITICAL" for c in c_flags):
            priority = "CRITICAL"
        elif risk_score >= ALERT_PRIORITY_THRESHOLDS["HIGH"] or any(c["severity"] == "HIGH" for c in c_flags):
            priority = "HIGH"
        else:
            priority = "MEDIUM"

        # Build Evidence Package
        evidence = {
            "risk_drivers": str(work.get("top_contributing_factors", "")).split("; "),
            "threshold_breached": f"Project Risk Score {risk_score:.1f} >= {ALERT_PRIORITY_THRESHOLDS[priority]}",
            "delay_probability_pct": round(float(work.get("delay_probability", 0.0) or 0.0) * 100, 1),
            "expected_delay_days": int(work.get("expected_delay_days", 0) or 0),
            "compliance_flags_count": len(c_flags),
            "compliance_rules_triggered": [c["rule_code"] for c in c_flags],
            "compliance_actions": [c["action"] for c in c_flags],
            "ml_anomaly_score": float(m_flag.get("ml_anomaly_score", 0.0) or 0.0) if m_flag else 0.0,
            "statistical_anomaly_score": float(s_flag.get("statistical_anomaly_score", 0.0) or 0.0) if s_flag else 0.0,
            "recommended_monitoring_priority": str(work.get("recommended_monitoring_priority", priority))
        }

        alert_id = f"ALT_{wid.replace('WORK_HASH_', '')}"

        alerts.append({
            "alert_id": alert_id,
            "canonical_work_id": wid,
            "source_house": work.get("source_house", "LOK_SABHA"),
            "canonical_state": work.get("canonical_state", "UNKNOWN"),
            "canonical_mp_name": work.get("canonical_mp_name", "UNKNOWN"),
            "priority": priority,
            "project_risk_score": risk_score,
            "delay_probability": float(work.get("delay_probability", 0.0) or 0.0),
            "expected_delay_days": int(work.get("expected_delay_days", 0) or 0),
            "status": "NEW",
            "evidence_json": json.dumps(evidence),
            "auditor_notes": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })

    df_alerts = pd.DataFrame(alerts)
    return df_alerts

