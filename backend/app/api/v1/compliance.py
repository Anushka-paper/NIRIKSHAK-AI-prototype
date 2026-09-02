import os
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

_VIOLATIONS_CACHE = None
_VIOLATIONS_MTIME = 0

def load_violations_df():
    global _VIOLATIONS_CACHE, _VIOLATIONS_MTIME
    path = os.path.join(DATA_DIR, "compliance", "compliance_violations.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
        
    mtime = os.path.getmtime(path)
    if _VIOLATIONS_CACHE is not None and _VIOLATIONS_MTIME == mtime:
        return _VIOLATIONS_CACHE

    df = pd.read_csv(path, low_memory=False)
    
    # Enrich UNKNOWN state and mp_name from unified_work_lifecycle.csv if available
    master_path = os.path.join(DATA_DIR, "integrated", "master", "unified_work_lifecycle.csv")
    if os.path.exists(master_path) and not df.empty:
        try:
            df_master = pd.read_csv(master_path, usecols=["canonical_work_id", "canonical_state", "canonical_mp_name"], low_memory=False)
            df_master = df_master.drop_duplicates(subset=["canonical_work_id"])
            
            # Extract clean work ID from entity_id e.g. "WS/ MP005/2024-2025/145074" or "WORK_HASH_..."
            merged = df.merge(df_master, left_on="entity_id", right_on="canonical_work_id", how="left", suffixes=("", "_master"))
            if "canonical_state" in merged.columns:
                df["state"] = df["state"].replace(["UNKNOWN", "", None], pd.NA).fillna(merged["canonical_state"]).fillna("ALL INDIA")
            if "canonical_mp_name" in merged.columns:
                df["mp_name"] = df["mp_name"].replace(["UNKNOWN", "", None], pd.NA).fillna(merged["canonical_mp_name"]).fillna("MINISTRY / IDA AUDIT")
        except Exception as e:
            print("[COMPLIANCE API] Master enrichment warning:", e)
            
    _VIOLATIONS_CACHE = df
    _VIOLATIONS_MTIME = mtime
    return df

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

    # When no specific rule filter or search is active, interleave rules so the feed shows diverse rule codes
    if not rule_code and not search and not severity and not df.empty:
        groups = [group for _, group in df.groupby("rule_code")]
        groups.sort(key=lambda g: len(g))  # rarer rules (R007, R008, R001, R002) first
        interleaved = []
        max_len = max(len(g) for g in groups) if groups else 0
        for i in range(max_len):
            for g in groups:
                if i < len(g):
                    interleaved.append(g.iloc[i])
        if interleaved:
            df = pd.DataFrame(interleaved)

    page_df = df.iloc[offset:offset+limit]
    res = page_df.fillna("").to_dict(orient="records")

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(res),
        "violations": res
    }
