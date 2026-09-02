import os
import json
import pandas as pd
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/predictive", tags=["Predictive Modeling Layer"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

def load_predictive_df():
    path = os.path.join(DATA_DIR, "predictive", "predictive_risk_scores.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

@router.get("/summary")
def get_predictive_summary():
    """Returns predictive modeling report and risk categories breakdown."""
    rep_path = os.path.join(DATA_DIR, "reports", "predictive_metrics_report.json")
    if os.path.exists(rep_path):
        with open(rep_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    df = load_predictive_df()
    if df.empty:
        return {"status": "SUCCESS", "total_works_evaluated": 0, "risk_category_breakdown": {}}
        
    return {
        "status": "SUCCESS",
        "total_works_evaluated": len(df),
        "high_risk_projects_count": int((df["project_risk_score"] >= 50.0).sum()),
        "critical_risk_projects_count": int((df["project_risk_score"] >= 75.0).sum()),
        "risk_category_breakdown": df["risk_category"].value_counts().to_dict() if "risk_category" in df.columns else {}
    }

@router.get("/risk-scores")
def query_predictive_risk_scores(
    risk_category: Optional[str] = Query(None, description="Filter risk category: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'"),
    house: Optional[str] = Query(None, description="House filter: 'LOK_SABHA' or 'RAJYA_SABHA'"),
    category: Optional[str] = Query(None, description="Work category filter"),
    search: Optional[str] = Query(None, description="Search Work ID or MP Name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500)
):
    """Query predictive risk scores and forecasts."""
    df = load_predictive_df()
    if df.empty:
        return {"total": 0, "returned": 0, "records": []}

    if risk_category:
        df = df[df["risk_category"].astype(str).str.upper() == risk_category.upper()]

    if house:
        df = df[df["source_house"].astype(str).str.upper() == house.upper()]

    if category:
        df = df[df["canonical_work_category"].astype(str).str.upper() == category.upper()]

    if search:
        s_upper = search.strip().upper()
        id_match = df["canonical_work_id"].astype(str).str.upper().str.contains(s_upper, na=False)
        mp_match = df["canonical_mp_name"].astype(str).str.upper().str.contains(s_upper, na=False) if "canonical_mp_name" in df.columns else False
        df = df[id_match | mp_match]

    total_count = len(df)
    page_df = df.iloc[offset:offset+limit]

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "returned": len(page_df),
        "records": page_df.fillna("").to_dict(orient="records")
    }
