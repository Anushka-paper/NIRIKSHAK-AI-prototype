from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.session import get_db
from db.models import WorkRecommended, Expenditure, VendorMaster, MPMaster

router = APIRouter()

@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Returns top-level stats for the frontend dashboard."""
    
    total_works = db.query(func.count(WorkRecommended.work_id)).scalar()
    
    total_budget_paise = db.query(func.sum(WorkRecommended.recommended_amount)).scalar() or 0
    total_budget_cr = round((total_budget_paise / 100) / 10000000, 2)
    
    total_expenditure_paise = db.query(func.sum(Expenditure.amount)).scalar() or 0
    total_expenditure_cr = round((total_expenditure_paise / 100) / 10000000, 2)
    
    total_vendors = db.query(func.count(VendorMaster.vendor_id)).scalar()
    
    # Calculate simple utilization percentage
    utilization_pct = 0
    if total_budget_paise > 0:
        utilization_pct = round((total_expenditure_paise / total_budget_paise) * 100, 1)

    return {
        "total_works": total_works,
        "total_budget_cr": total_budget_cr,
        "total_expenditure_cr": total_expenditure_cr,
        "total_vendors": total_vendors,
        "utilization_pct": utilization_pct,
        # Mock risk stats since Phase 5 isn't done yet
        "high_risk_works": int(total_works * 0.05) if total_works else 0,
        "alerts_open": 24
    }
