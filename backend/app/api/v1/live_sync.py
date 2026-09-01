from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.session import get_db
from ingestion.live_sync import sync_live_data

router = APIRouter()

@router.post("/trigger")
def trigger_live_sync(
    house: str = Query("all", description="House filter: 'all', 'lok_sabha', 'rajya_sabha'"),
    db: Session = Depends(get_db)
):
    """Triggers real-time incremental data sync from official eSAKSHI live portal."""
    result = sync_live_data(db, house_filter=house)
    return result

@router.get("/status")
def get_sync_status(db: Session = Depends(get_db)):
    """Returns status of live sync engine and latest record counts."""
    from db.models import WorkRecommended
    
    ls_count = db.query(WorkRecommended).filter(WorkRecommended.house == "Lok Sabha").count()
    rs_count = db.query(WorkRecommended).filter(WorkRecommended.house == "Rajya Sabha").count()
    
    return {
        "status": "active",
        "live_engine": "SHA-256 Incremental Sync",
        "source_url": "https://mplads.mospi.gov.in/digigov/dashboard.html",
        "lok_sabha_works": ls_count,
        "rajya_sabha_works": rs_count,
        "total_works": ls_count + rs_count
    }

