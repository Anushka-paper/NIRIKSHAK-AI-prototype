import os
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/works/duplicates", tags=["Duplicate Payment Detector (§10, §11)"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

_DUPLICATES_CACHE = None
_DUPLICATES_MTIME = 0

def load_duplicates_df():
    global _DUPLICATES_CACHE, _DUPLICATES_MTIME
    path = os.path.join(DATA_DIR, "compliance", "duplicate_payments.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
        
    mtime = os.path.getmtime(path)
    if _DUPLICATES_CACHE is not None and _DUPLICATES_MTIME == mtime:
        return _DUPLICATES_CACHE

    df = pd.read_csv(path, low_memory=False)
    _DUPLICATES_CACHE = df
    _DUPLICATES_MTIME = mtime
    return df

@router.get("")
def query_duplicate_payments(
    layer_type: Optional[str] = Query(None, description="Layer filter: 'EXACT', 'NEAR', 'REPEATED_AMOUNT', 'SAMEDAY_VENDOR'"),
    status: Optional[str] = Query(None, description="Status filter: 'NEW', 'CONFIRMED_DUPLICATE', 'LEGITIMATE_RATE_CARD', 'REJECTED'"),
    search: Optional[str] = Query(None, description="Search in duplicate_id, canonical_work_id, work_name, or vendor_name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """List duplicate payment candidate flags with contextual rate-card indicators (§10, §11)."""
    df = load_duplicates_df()
    if df.empty:
        return {"total": 0, "returned": 0, "duplicates": []}

    if layer_type:
        df = df[df["layer_type"].astype(str).str.upper() == layer_type.upper()]

    if status:
        df = df[df["status"].astype(str).str.upper() == status.upper()]

    if search:
        s_upper = search.strip().upper()
        id_match = df["duplicate_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        work_match = df["canonical_work_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        vendor_match = df["vendor_name"].astype(str).str.upper().str.contains(s_upper, na=False)
        name_match = df["work_name"].astype(str).str.upper().str.contains(s_upper, na=False) if "work_name" in df.columns else False
        df = df[id_match | work_match | vendor_match | name_match]

    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    res = page_df.fillna("").to_dict(orient="records")

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(res),
        "duplicates": res
    }

@router.post("/{duplicate_id}/review")
def review_duplicate_flag(
    duplicate_id: str,
    review: dict = Body(...)
):
    """
    Human/auditor review endpoint (§10, §11).
    Confirm or reject duplicate payment flags (CONFIRMED_DUPLICATE / LEGITIMATE_RATE_CARD / REJECTED).
    """
    df = load_duplicates_df()
    if df.empty:
        raise HTTPException(status_code=404, detail="Duplicate data store empty")

    new_status = review.get("status", "CONFIRMED_DUPLICATE")
    notes = review.get("auditor_notes", "")

    valid_statuses = ["NEW", "CONFIRMED_DUPLICATE", "LEGITIMATE_RATE_CARD", "REJECTED"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    mask = df["duplicate_id"].astype(str).str.upper() == duplicate_id.upper()
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"Duplicate ID '{duplicate_id}' not found")

    df.loc[mask, "status"] = new_status
    if "auditor_notes" not in df.columns:
        df["auditor_notes"] = ""
    df.loc[mask, "auditor_notes"] = notes

    path = os.path.join(DATA_DIR, "compliance", "duplicate_payments.csv")
    df.to_csv(path, index=False, encoding="utf-8")

    global _DUPLICATES_CACHE
    _DUPLICATES_CACHE = df

    updated_row = df[mask].fillna("").to_dict(orient="records")[0]
    return {
        "status": "SUCCESS",
        "message": f"Duplicate '{duplicate_id}' review status updated to '{new_status}'.",
        "duplicate": updated_row
    }
