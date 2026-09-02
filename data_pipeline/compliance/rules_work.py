import numpy as np
import pandas as pd
from data_pipeline.compliance.config import COMPLIANCE_RULES

def evaluate_work_rules(df_work, df_lifecycle):
    violations = []
    if df_work.empty:
        return violations
        
    avail_cols = [c for c in ["canonical_work_id", "source_house", "canonical_state", "canonical_mp_name", "recommended_amount_inr", "sanctioned_amount_inr", "expenditure_amount_inr", "image"] if c in df_lifecycle.columns] if not df_lifecycle.empty else []
    
    # Fill source_house from df_work if missing
    merged = df_work.merge(df_lifecycle[avail_cols], on="canonical_work_id", how="left", suffixes=("", "_life")) if avail_cols else df_work.copy()
    if "source_house" not in merged.columns and "source_house_life" in merged.columns:
        merged["source_house"] = merged["source_house_life"]

    # R002: EXP_EXCEEDS_SANCTION
    sanc_amt = pd.to_numeric(merged.get("sanctioned_amount_inr", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)
    exp_amt = pd.to_numeric(merged.get("expenditure_amount_inr", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)
    overrun = pd.to_numeric(merged.get("overrun_pct", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)

    cond_r002 = ((sanc_amt > 0) & (exp_amt > sanc_amt)) | (overrun > 0)
    df_r002 = merged[cond_r002]
    for _, row in df_r002.iterrows():
        violations.append({
            "rule_code": "R002",
            "rule_name": COMPLIANCE_RULES["R002"]["name"],
            "severity": COMPLIANCE_RULES["R002"]["severity"],
            "weight": COMPLIANCE_RULES["R002"]["weight"],
            "entity_type": "WORK",
            "entity_id": str(row["canonical_work_id"]),
            "source_house": str(row.get("source_house", "LOK_SABHA")),
            "state": str(row.get("canonical_state", "UNKNOWN")),
            "mp_name": str(row.get("canonical_mp_name", "UNKNOWN")),
            "description": f"Expenditure ₹{float(row.get('expenditure_amount_inr', 0.0) or 0.0):,.2f} exceeds sanctioned amount ₹{float(row.get('sanctioned_amount_inr', 0.0) or 0.0):,.2f}",
            "action": COMPLIANCE_RULES["R002"]["action"]
        })

    # R003: MISSING_SANCTION_BEFORE_EXP
    has_sanc = merged.get("has_sanction", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    has_exp = merged.get("has_expenditure", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    cond_r003 = has_exp & (~has_sanc)
    df_r003 = merged[cond_r003]
    for _, row in df_r003.iterrows():
        violations.append({
            "rule_code": "R003",
            "rule_name": COMPLIANCE_RULES["R003"]["name"],
            "severity": COMPLIANCE_RULES["R003"]["severity"],
            "weight": COMPLIANCE_RULES["R003"]["weight"],
            "entity_type": "WORK",
            "entity_id": str(row["canonical_work_id"]),
            "source_house": str(row.get("source_house", "LOK_SABHA")),
            "state": str(row.get("canonical_state", "UNKNOWN")),
            "mp_name": str(row.get("canonical_mp_name", "UNKNOWN")),
            "description": "Expenditure recorded on work without sanction approval",
            "action": COMPLIANCE_RULES["R003"]["action"]
        })

    # R004: SANCTION_BEFORE_REC
    sanc_delay = pd.to_numeric(merged.get("sanction_delay_days", pd.Series(np.nan, index=merged.index)), errors="coerce")
    cond_r004 = sanc_delay.notna() & (sanc_delay < 0)
    df_r004 = merged[cond_r004]
    for _, row in df_r004.iterrows():
        violations.append({
            "rule_code": "R004",
            "rule_name": COMPLIANCE_RULES["R004"]["name"],
            "severity": COMPLIANCE_RULES["R004"]["severity"],
            "weight": COMPLIANCE_RULES["R004"]["weight"],
            "entity_type": "WORK",
            "entity_id": str(row["canonical_work_id"]),
            "source_house": str(row.get("source_house", "LOK_SABHA")),
            "state": str(row.get("canonical_state", "UNKNOWN")),
            "mp_name": str(row.get("canonical_mp_name", "UNKNOWN")),
            "description": f"Sanction date precedes recommendation date by {abs(float(row['sanction_delay_days'])):.0f} days",
            "action": COMPLIANCE_RULES["R004"]["action"]
        })

    # R005: COMPLETION_BEFORE_SANCTION
    comp_delay = pd.to_numeric(merged.get("completion_delay_days", pd.Series(np.nan, index=merged.index)), errors="coerce")
    cond_r005 = comp_delay.notna() & (comp_delay < 0)
    df_r005 = merged[cond_r005]
    for _, row in df_r005.iterrows():
        violations.append({
            "rule_code": "R005",
            "rule_name": COMPLIANCE_RULES["R005"]["name"],
            "severity": COMPLIANCE_RULES["R005"]["severity"],
            "weight": COMPLIANCE_RULES["R005"]["weight"],
            "entity_type": "WORK",
            "entity_id": str(row["canonical_work_id"]),
            "source_house": str(row.get("source_house", "LOK_SABHA")),
            "state": str(row.get("canonical_state", "UNKNOWN")),
            "mp_name": str(row.get("canonical_mp_name", "UNKNOWN")),
            "description": f"Completion date precedes sanction date by {abs(float(row['completion_delay_days'])):.0f} days",
            "action": COMPLIANCE_RULES["R005"]["action"]
        })

    # R008: MISSING_COMPLETION_EVIDENCE
    has_comp = merged.get("has_completion", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    img_str = merged.get("image", pd.Series("", index=merged.index)).astype(str).str.strip().str.lower()
    cond_r008 = has_comp & (img_str.isin(["", "nan", "none"]))
    df_r008 = merged[cond_r008]
    for _, row in df_r008.iterrows():
        violations.append({
            "rule_code": "R008",
            "rule_name": COMPLIANCE_RULES["R008"]["name"],
            "severity": COMPLIANCE_RULES["R008"]["severity"],
            "weight": COMPLIANCE_RULES["R008"]["weight"],
            "entity_type": "WORK",
            "entity_id": str(row["canonical_work_id"]),
            "source_house": str(row.get("source_house", "LOK_SABHA")),
            "state": str(row.ge