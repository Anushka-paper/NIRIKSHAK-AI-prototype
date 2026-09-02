import os
import json
import pandas as pd
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/features", tags=["Canonical Feature Store"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "features"))

@router.get("/summary")
def get_feature_store_summary():
    """Returns canonical feature store record counts and version."""
    dict_path = os.path.join(DATA_DIR, "feature_dictionary.json")
    dict_data = json.load(open(dict_path, "r", encoding="utf-8")) if os.path.exists(dict_path) else {}
    
    fw_path = os.path.join(DATA_DIR, "features_work.csv")
    ft_path = os.path.join(DATA_DIR, "features_transaction.csv")
    fv_path = os.path.join(DATA_DIR, "features_vendor.csv")
    fm_path = os.path.join(DATA_DIR, "features_mp.csv")
    
    return {
        "status": "SUCCESS",
        "feature_version": dict_data.get("version", "v1.0"),
        "tables": {
            "features_work": len(pd.read_csv(fw_path, low_memory=False)) if os.path.exists(fw_path) else 0,
            "features_transaction": len(pd.read_csv(ft_path, low_memory=False)) if os.path.exists(ft_path) else 0,
            "features_vendor": len(pd.read_csv(fv_path, low_memory=False)) if os.path.exists(fv_path) else 0,
            "features_mp": len(pd.read_csv(fm_path, low_memory=False)) if os.path.exists(fm_path) else 0
        }
    }

@router.get("/work")
def query_work_features(
    house: Optional[str] = Query(None, description="House filter: 'LOK_SABHA' or 'RAJYA_SABHA'"),
    category: Optional[str] = Query(None, description="Category filter"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query features_work table."""
    path = os.path.join(DATA_DIR, "features_work.csv")
    if not os.path.exists(path):
        return {"total": 0, "returned": 0, "records": []}
        
    df = pd.read_csv(path, low_memory=False)
    if house:
        df = df[df["source_house"].astype(str).str.upper() == house.upper()]
    if category:
        df = df[df["canonical_work_category"].astype(str).str.upper() == category.upper()]
        
    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(page_df),
        "records": page_df.fillna("").to_dict(orient="records")
    }

@router.get("/vendor")
def query_vendor_features(
    search: Optional[str] = Query(None, description="Search vendor name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query features_vendor table."""
    path = os.path.join(DATA_DIR, "features_vendor.csv")
    if not os.path.exists(path):
        return {"total": 0, "returned": 0, "records": []}
        
    df = pd.read_csv(path, low_memory=False)
    if search:
        s_upper = search.strip().upper()
        df = df[df["canonical_name"].astype(str).str.upper().str.contains(s_upper, na=False)]
        
    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(page_df),
        "records": page_df.fillna("").to_dict(orient="records")
    }

@router.get("/mp")
def query_mp_features(
    house: Optional[str] = Query(None, description="House filter"),
    search: Optional[str] = Query(None, description="Search MP name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query features_mp table."""
    path = os.path.join(DATA_DIR, "features_mp.csv")
    if not os.path.exists(path):
        return {"total": 0, "returned": 0, "records": []}
        
    df = pd.read_csv(path, low_memory=False)
    if house:
        df = df[df["source_house"].astype(str).str.upper() == house.upper()]
    if search:
        s_upper = search.strip().upper()
        df = df[df["canonical_name"].astype(str).str.upper().str.contains(s_upper, na=False)]
        
    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(page_df),
        "records": page_df.fillna("").to_dict(orient="records")
    }

