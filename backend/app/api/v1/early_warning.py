import os
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/early-warning", tags=["Early Warning Engine"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

_ALERTS_CACHE = None
_ALERTS_MTIME = 0

def load_alerts_df():
    global _ALERTS_CACHE, _ALERTS_MTIME
    path = os.path.join(DATA_DIR, "early_warning", "alerts.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
        
    mtime = os.path.getmtime(path)
    if _ALERTS_CACHE is not None and _ALERTS_MTIME == mtime:
        return _ALERTS_CACHE

    df = pd.read_csv(path, low_memory=False)
    _ALERTS_CACHE = df
    _ALERTS_MTIME = mtime
    return df

@router.get("/summary")
def get_early_warning_summary():
    """Returns top-level early-warning alert summary and priority/status breakdown."""
    rep_path = os.path.join(DATA_DIR, "reports", "early_warning_report.json")
    if os.path.exists(rep_path):
        with open(rep_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    df = load_alerts_df()
    if df.empty:
        return {"status": "SUCCESS", "total_alerts_generated": 0, "priority_breakdown": {}, "status_breakdown": {}}
        
    return {
        "status": "SUCCESS",
        "total_alerts_generated": len(df),
        "priority_breakdown": df["priority"].value_counts().to_dict() if "priority" in df.columns else {},
        "status_breakdown": df["status"].value_counts().to_dict() if "status" in df.columns else {}
    }

@router.get("/alerts")
def query_early_warning_alerts(
    priority: Optional[str] = Query(None, description="Priority filter: 'CRITICAL', 'HIGH', 'MEDIUM'"),
    status: Optional[str] = Query(None, description="Status filter: 'NEW', 'UNDER_INVESTIGATION', 'VALIDATED_RISK', 'DISMISSED', 'DATA_QUALITY_ISSUE'"),
    house: Optional[str] = Query(None, description="House filter e.g. 'LOK_SABHA', 'RAJYA_SABHA'"),
    search: Optional[str] = Query(None, description="Search in alert_id, canonical_work_id, or canonical_mp_name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query early warning alert objects and evidence payloads (§14, §24)."""
    df = load_alerts_df()
    if df.empty:
        return {"total": 0, "returned": 0, "alerts": []}

    if priority:
        df = df[df["priority"].astype(str).str.upper() == priority.upper()]

    if status:
        df = df[df["status"].astype(str).str.upper() == status.upper()]

    if house and house.upper() != "ALL":
        df = df[df["source_house"].astype(str).str.upper() == house.upper()]

    if search:
        s_upper = search.strip().upper()
        id_match = df["alert_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        work_match = df["canonical_work_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        mp_match = df["canonical_mp_name"].astype(str).str.upper().str.contains(s_upper, na=False)
        df = df[id_match | work_match | mp_match]

    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    res = page_df.fillna("").to_dict(orient="records")

    # Parse evidence_json string to dict for API consumers
    for item in res:
        if isinstance(item.get("evidence_json"), str) and item["evidence_json"]:
            try:
                item["evidence"] = json.loads(item["evidence_json"])
            except Exception:
                item["evidence"] = {}
        else:
            item["evidence"] = {}

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(res),
        "alerts": res
    }

@router.post("/alerts/{alert_id}/feedback")
def submit_human_auditor_feedback(
    alert_id: str,
    feedback: dict = Body(...)
):
    """
    Human/auditor investigation feedback loop (§21).
    Analyst marks alert as VALIDATED_RISK / DISMISSED / DATA_QUALITY_ISSUE / UNDER_INVESTIGATION.
    """
    df = load_alerts_df()
    if df.empty:
        raise HTTPException(status_code=404, detail="Alert data store empty")

    new_status = feedback.get("status", "UNDER_INVESTIGATION")
    notes = feedback.get("auditor_notes", "")
    auditor_id = feedback.get("auditor_id", "ANALYST_01")

    valid_statuses = ["NEW", "UNDER_INVESTIGATION", "VALIDATED_RISK", "DISMISSED", "DATA_QUALITY_ISSUE"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    mask = df["alert_id"].astype(str).str.upper() == alert_id.upper()
    if not mask.any():
        # Fallback search by canonical_work_id
        mask = df["canonical_work_id"].astype(str).str.upper() == alert_id.upper()
        if not mask.any():
            raise HTTPException(status_code=404, detail=f"Alert ID '{alert_id}' not found")

    df.loc[mask, "status"] = new_status
    df.loc[mask, "auditor_notes"] = notes
    df.loc[mask, "updated_at"] = datetime.now().isoformat()

    # Save back to CSV
    path = os.path.join(DATA_DIR, "early_warning", "alerts.csv")
    df.to_csv(path, index=False, encoding="utf-8")

    # Clear cache
    global _ALERTS_CACHE
    _ALERTS_CACHE = df

    updated_row = df[mask].fillna("").to_dict(orient="records")[0]
    return {
        "status": "SUCCESS",
        "message": f"Alert '{alert_id}' updated to '{new_status}' with auditor notes.",
        "alert": updated_row
    }

