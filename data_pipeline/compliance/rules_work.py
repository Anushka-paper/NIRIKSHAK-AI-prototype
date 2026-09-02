import numpy as np
import pandas as pd
from data_pipeline.compliance.config import COMPLIANCE_RULES

def evaluate_work_rules(df_work, df_lifecycle):
    violations = []
    if df_work.empty:
        return violations
        
    avail_cols = [c for c in ["canonical_work_id", "source_house", "canonical_state", "canonical_mp_name", "recommended_amount_inr", "sanctioned_amount_inr", "expenditure_amount_inr", "image"] if c in df_lifecycle.columns] if not df_lifecycle.empty else []
    
    if avail_cols:
        df_life_sub = df_lifecycle[avail_cols].drop_duplicates(subset=["canonical_work_id"])
        merged = df_work.merge(df_life_sub, on="canonical_work_id", how="left", suffixes=("", "_life"))
    else:
        merged = df_work.copy()
        
    if "source_house" not in merged.columns and "source_house_life" in merged.columns:
        merged["source_house"] = merged["source_house_life"]
    merged["source_house"] = merged.get("source_house", pd.Series("LOK_SABHA", index=merged.index)).fillna("LOK_SABHA")
    
    if "canonical_state_life" in merged.columns:
        merged["canonical_state"] = merged["canonical_state"].replace(["UNKNOWN", "", None], np.nan).fillna(merged["canonical_state_life"]).fillna("UNKNOWN")
    else:
        merged["canonical_state"] = merged.get("canonical_state", pd.Series("UNKNOWN", index=merged.index)).fillna("UNKNOWN")

    if "canonical_mp_name_life" in merged.columns:
        merged["canonical_mp_name"] = merged["canonical_mp_name"].replace(["UNKNOWN", "", None], np.nan).fillna(merged["canonical_mp_name_life"]).fillna("UNKNOWN")
    else:
        merged["canonical_mp_name"] = merged.get("canonical_mp_name", pd.Series("UNKNOWN", index=merged.index)).fillna("UNKNOWN")

    # R002: EXP_EXCEEDS_SANCTION
    sanc_amt = pd.to_numeric(merged.get("sanctioned_amount_inr", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)
    exp_amt = pd.to_numeric(merged.get("expenditure_amount_inr", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)
    overrun = pd.to_numeric(merged.get("overrun_pct", pd.Series(0.0, index=merged.index)), errors="coerce").fillna(0.0)

    cond_r002 = ((sanc_amt > 0) & (exp_amt > sanc_amt)) | (overrun > 0)
    df_r002 = merged[cond_r002]
    if not df_r002.empty:
        for r in df_r002.to_dict(orient="records"):
            violations.append({
                "rule_code": "R002",
                "rule_name": COMPLIANCE_RULES["R002"]["name"],
                "severity": COMPLIANCE_RULES["R002"]["severity"],
                "weight": COMPLIANCE_RULES["R002"]["weight"],
                "entity_type": "WORK",
                "entity_id": str(r["canonical_work_id"]),
                "source_house": str(r["source_house"]),
                "state": str(r["canonical_state"]),
                "mp_name": str(r["canonical_mp_name"]),
                "description": f"Expenditure ₹{float(r.get('expenditure_amount_inr', 0.0) or 0.0):,.2f} exceeds sanctioned amount ₹{float(r.get('sanctioned_amount_inr', 0.0) or 0.0):,.2f}",
                "action": COMPLIANCE_RULES["R002"]["action"]
            })

    # R003: MISSING_SANCTION_BEFORE_EXP
    has_sanc = merged.get("has_sanction", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    has_exp = merged.get("has_expenditure", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    cond_r003 = has_exp & (~has_sanc)
    df_r003 = merged[cond_r003]
    if not df_r003.empty:
        for r in df_r003.to_dict(orient="records"):
            violations.append({
                "rule_code": "R003",
                "rule_name": COMPLIANCE_RULES["R003"]["name"],
                "severity": COMPLIANCE_RULES["R003"]["severity"],
                "weight": COMPLIANCE_RULES["R003"]["weight"],
                "entity_type": "WORK",
                "entity_id": str(r["canonical_work_id"]),
                "source_house": str(r["source_house"]),
                "state": str(r["canonical_state"]),
                "mp_name": str(r["canonical_mp_name"]),
                "description": "Expenditure recorded on work without sanction approval",
                "action": COMPLIANCE_RULES["R003"]["action"]
            })

    # R004: SANCTION_BEFORE_REC
    sanc_delay = pd.to_numeric(merged.get("sanction_delay_days", pd.Series(np.nan, index=merged.index)), errors="coerce")
    cond_r004 = sanc_delay.notna() & (sanc_delay < 0)
    df_r004 = merged[cond_r004]
    if not df_r004.empty:
        for r in df_r004.to_dict(orient="records"):
            violations.append({
                "rule_code": "R004",
                "rule_name": COMPLIANCE_RULES["R004"]["name"],
                "severity": COMPLIANCE_RULES["R004"]["severity"],
                "weight": COMPLIANCE_RULES["R004"]["weight"],
                "entity_type": "WORK",
                "entity_id": str(r["canonical_work_id"]),
                "source_house": str(r["source_house"]),
                "state": str(r["canonical_state"]),
                "mp_name": str(r["canonical_mp_name"]),
                "description": f"Sanction date precedes recommendation date by {abs(float(r['sanction_delay_days'])):.0f} days",
                "action": COMPLIANCE_RULES["R004"]["action"]
            })

    # R005: COMPLETION_BEFORE_SANCTION
    comp_delay = pd.to_numeric(merged.get("completion_delay_days", pd.Series(np.nan, index=merged.index)), errors="coerce")
    cond_r005 = comp_delay.notna() & (comp_delay < 0)
    df_r005 = merged[cond_r005]
    if not df_r005.empty:
        for r in df_r005.to_dict(orient="records"):
            violations.append({
                "rule_code": "R005",
                "rule_name": COMPLIANCE_RULES["R005"]["name"],
                "severity": COMPLIANCE_RULES["R005"]["severity"],
                "weight": COMPLIANCE_RULES["R005"]["weight"],
                "entity_type": "WORK",
                "entity_id": str(r["canonical_work_id"]),
                "source_house": str(r["source_house"]),
                "state": str(r["canonical_state"]),
                "mp_name": str(r["canonical_mp_name"]),
                "description": f"Completion date precedes sanction date by {abs(float(r['completion_delay_days'])):.0f} days",
                "action": COMPLIANCE_RULES["R005"]["action"]
            })

    # R008: MISSING_COMPLETION_EVIDENCE
    has_comp = merged.get("has_completion", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    img_str = merged.get("image", pd.Series("", index=merged.index)).astype(str).str.strip().str.lower()
    cond_r008 = has_comp & (img_str.isin(["", "nan", "none"]))
    df_r008 = merged[cond_r008]
    if not df_r008.empty:
        for r in df_r008.to_dict(orient="records"):
            violations.append({
                "rule_code": "R008",
                "rule_name": COMPLIANCE_RULES["R008"]["name"],
                "severity": COMPLIANCE_RULES["R008"]["severity"],
                "weight": COMPLIANCE_RULES["R008"]["weight"],
                "entity_type": "WORK",
                "entity_id": str(r["canonical_work_id"]),
                "source_house": str(r["source_house"]),
                "state": str(r["canonical_state"]),
                "mp_name": str(r["canonical_mp_name"]),
                "description": "Work marked completed without photographic or documentary evidence",
                "action": COMPLIANCE_RULES["R008"]["action"]
            })

    return violations
