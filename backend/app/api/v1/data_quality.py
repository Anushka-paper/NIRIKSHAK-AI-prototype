from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.session import get_db
from ingestion.validation.validator import DataValidator

router = APIRouter()

@router.get("/")
def get_data_quality_report(
    house: str = Query("all", description="House filter: 'all', 'lok_sabha', or 'rajya_sabha'"),
    db: Session = Depends(get_db)
):
    """Runs data quality validation checks across all ingested datasets for specified house."""
    validator = DataValidator(db, house=house)
    report = validator.run_all_checks()
    return report
