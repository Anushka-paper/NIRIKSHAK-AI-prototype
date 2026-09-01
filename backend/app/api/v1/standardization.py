import os
import glob
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from data_pipeline.standardisation.pipeline import run_standardisation_pipeline

router = APIRouter(prefix="/standardization", tags=["Data Standardization"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "standardised"))

def load_master_lifecycle_df():
    master_path = os.path.join(DATA_DIR, "master", "unified_work_lifecycle.csv")
    if not os.path.exists(master_path):
        return pd.DataFrame()
    return pd.read_csv(master_path, low_memory=False)

@router.post("/run")
def trigger_data_standardization():
    """
    Triggers canonical data standardisation pipeline across all 12 Lok Sabha & Rajya Sabha datasets.
    Generates canonical ISO dates (YYYY-MM-DD), numeric INR amounts, category taxonomy, and master work lifecycle.
    """
    run_standardisation_pipeline()
    df_m = load_master_lifecycle_df()
    
    return {
        "status": "success",
        "message": "Data standardisation pipeline executed successfully across Lok Sabha & Rajya Sabha datasets.",
        "master_lifecycle_works_built": len(df_m)
    }

@router.get("/summary")
def get_standardization_summary():
    """
    Returns empirical row counts and lifecycle stage distributions for all standardized datasets.
    """
    ls_files = glob.glob(os.path.join(DATA_DIR, "lok_sabha", "std_*.csv"))
    rs_files = glob.glob(os.path.join(DATA_DIR, "rajya_sabha", "std_*.csv"))
    df_m = load_master_lifecycle_df()
    
    ls_counts = {}
    for f in ls_files:
        ds_name = os.path.basename(f).replace("std_", "").replace(".csv", "")
        ls_counts[ds_name] = len(pd.read_csv(f, low_memory=False))
        
    rs_counts = {}
    for f in rs_files:
        ds_name = os.path.basename(f).replace("std_", "").replace(".csv", "")
        rs_counts[ds_name] = len(pd.read_csv(f, low_memory=False))

    lifecycle_breakdown = {}
    if not df_m.empty and "lifecycle_stage" in df_m.columns:
        lifecycle_breakdown = df_m["lifecycle_stage"].value_counts().to_dict()

    return {
        "status": "SUCCESS",
        "lok_sabha": {
            "total_datasets": len(ls_files),
            "dataset_rows": ls_counts
        },
        "rajya_sabha": {
            "total_datasets": len(rs_files),
            "dataset_rows": rs_counts
        },
        "unified_master_lifecycle": {
            "total_unified_works": len(df_m),
            "lifecycle_stages": lifecycle_breakdown
        }
    }

@router.get("/master-works")
def query_master_works(
    house: Optional[str] = Query(None, description="House filter: 'LOK_SABHA' or 'RAJYA_SABHA'"),
    lifecycle_stage: Optional[str] = Query(None, description="Lifecycle stage: 'RECOMMENDED', 'SANCTIONED', 'IN_PROGRESS', 'COMPLETED'"),
    category: Optional[str] = Query(None, description="Category filter e.g. 'ROADS_AND_BRIDGES', 'DRINKING_WATER'"),
    state: Optional[str] = Query(None, description="State name e.g. 'MAHARASHTRA'"),
    search: Optional[str] = Query(None, description="Search in work title or MP name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Search and filter standardized unified master work records.
    """
    df = load_master_lifecycle_df()
    if df.empty:
        return {"total": 0, "returned": 0, "works": []}
        
    if house:
        df = df[df["source_house"].astype(str).str.upper() == house.upper()]
        
    if lifecycle_stage:
        df = df[df["lifecycle_stage"].astype(str).str.upper() == lifecycle_stage.upper()]

    if category:
        df = df[df["canonical_work_category"].astype(str).str.upper() == category.upper()]

    if state:
        df = df[df["canonical_state"].astype(str).str.upper() == state.upper()]
        
    if search:
        s_upper = search.strip().upper()
        work_match = df["work"].astype(str).str.upper().str.contains(s_upper, na=False)
        mp_match = df["canonical_mp_name"].astype(str).str.upper().str.contains(s_upper, na=False) if "canonical_mp_name" in df.columns else False
        df = df[work_match | mp_match]

    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]
    res = page_df.fillna("").to_dict(orient="records")
    
    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(res),
        "works": res
    }

@router.get("/preview")
def preview_standardization_rules():
    """Returns exact canonical taxonomy rules, status vocabularies, date/currency specs."""
    return {
        "canonical_date_format": "ISO-8601 (YYYY-MM-DD)",
        "canonical_currency_format": "Numeric INR Float (₹)",
        "category_taxonomy": [
            "ROADS_AND_BRIDGES",
            "DRINKING_WATER",
            "EDUCATION",
            "PUBLIC_HEALTH",
            "SANITATION",
            "OTHER_WORKS"
        ],
        "status_vocabulary": [
            "RECOMMENDED",
            "SANCTIONED",
            "IN_PROGRESS",
            "COMPLETED",
            "PAYMENT_SUCCESSFUL",
            "PAYMENT_PENDING"
        ],
        "identifier_strategy": {
            "work_id": "eSAKSHI Work ID or WORK_HASH_<md5>",
            "mp_id": "MP_<house>_<state>_<normalized_name>",
            "state_id": "STATE_<state_name>",
            "constituency_id": "CONST_<constituency_name>"
        }
    }
