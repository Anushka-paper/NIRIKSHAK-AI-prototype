import os
import pandas as pd
from fastapi import APIRouter, Query

router = APIRouter(prefix="/vendors", tags=["Vendor Intelligence Layer (§22)"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))

@router.get("/risk")
def get_vendor_risk_rankings(limit: int = Query(30, ge=1, le=100)):
    """Returns vendor concentration ranking, transaction profile & risk (§22)."""
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

