import os
import json
import pandas as pd
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/vendors", tags=["Vendor Intelligence Engine (§7, §22)"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

@router.get("/risk")
def get_vendor_risk_rankings(
    search: Optional[str] = Query(None, description="Search by vendor name or primary constituency"),
    limit: int = Query(30, ge=1, le=100)
):
    """
    Returns vendor concentration ranking, IsolationForest anomaly scores, 
    monopoly dependency ratios, and coefficient of variation (§7, §22).
    """
    rep_path = os.path.join(DATA_DIR, "reports", "vendor_risk_report.json")
    if os.path.exists(rep_path):
        try:
            with open(rep_path, "r", encoding="utf-8") as f:
                report = json.load(f)
                vendors = report.get("vendors", [])
                if search:
                    s_upper = search.strip().upper()
                    vendors = [
                        v for v in vendors
                        if s_upper in str(v.get("canonical_vendor_name", "")).upper() or
                           s_upper in str(v.get("primary_constituency", "")).upper()
                    ]
                report["returned"] = len(vendors[:limit])
                report["vendors"] = vendors[:limit]
                return report
        except Exception:
            pass

    master_path = os.path.join(DATA_DIR, "integrated", "master", "unified_work_lifecycle.csv")
    if not os.path.exists(master_path):
        return {"status": "insufficient_data", "vendors": []}

    df = pd.read_csv(master_path, low_memory=False)
    if "canonical_vendor_name" not in df.columns:
        return {"status": "insufficient_data", "vendors": []}

    df_vendors = df[df["canonical_vendor_name"].notna() & (df["canonical_vendor_name"].astype(str).str.strip() != "")]
    if df_vendors.empty:
        return {"status": "insufficient_data", "vendors": []}

    grp = df_vendors.groupby("canonical_vendor_name").agg(
        works_assigned=("canonical_work_id", "count"),
        total_disbursed_inr=("expenditure_amount_inr", lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum()),
        states_operating=("canonical_state", "nunique")
    ).reset_index()

    grp["total_disbursed_cr"] = (grp["total_disbursed_inr"] / 1e7).round(2)
    grp = grp.sort_values(by="works_assigned", ascending=False).head(limit)
    vendors = grp.to_dict(orient="records")

    return {
        "status": "SUCCESS",
        "total_vendors_tracked": len(grp),
        "vendors": vendors
    }
