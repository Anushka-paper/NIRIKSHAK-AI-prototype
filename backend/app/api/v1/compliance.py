import os
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

def load_violations_df():
    path = os.path.join(DATA_DIR, "compliance", "compliance_violations.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

@router.get("/summary")
def get_compliance_summary():
    """Returns top-level compliance violation summary and severity breakdown."""
    rep_path = os.path.join(DATA_DIR, "reports", "compliance_report.json")
    if os.path.exists(rep_path):
        with open(rep_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    df = load_violations_df()
    if df.empty:
        return {"status": "SUCCESS", "total_violations": 0, "severity_breakdown": {}, "rule_breakdown": {}}
        
    return {
        "status": "SUCCESS",
        "total_violations": len(df),
        "severity_breakdown": df["severity"].value_counts().to_dict() if "severity" in df.columns else {},
        "rule_breakdown": df["rule_code"].value_counts().to_dict() if "rule_code" in df.columns else {}
    }

@router.get("/violations")
def query_compliance_violations(
    severity: Optional[str] = Query(None, description="Severity filter: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'"),
    rule_code: Optional[str] = Query(None, description="Rule code filter e.g. 'R001', 'R002', 'R003', 'R007'"),
    search: Optional[str] = Query(None, description="Search in entity_id, description, or mp_name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query and filter compliance audit violations."""
    df = load_violations_df()
    if df.empty:
        return {"total": 0, "returned": 0, "violations": []}

    if severity:
        df = df[df["severity"].astype(str).str.upper() == severity.upper()]

    if rule_code:
        df = df[df["rule_code"].astype(str).str.upper() == rule_code.upper()]

    if search:
        s_upper = search.strip().upper()
        id_match = df["entity_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        desc_match = df["description"].astype(str).str.upper().str.contains(s_upper, na=False)
        mp_match = df["mp_name"].astype(str).str.upper().str.contains(s_upper, na=False) if "mp_name" in df.columns else False
        df = df[id_match | desc_match | mp_match]

    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    res = page_df.fillna("").to_dict(orient="records")

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(res),
        "violations": res
    }

