import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from db.session import get_db
from ingestion.standardization.standardizer import run_standardization_pipeline, DataStandardizer

router = APIRouter(prefix="/standardization", tags=["Data Standardization"])

@router.post("/run")
def trigger_data_standardization(db: Session = Depends(get_db)):
    """
    Triggers canonical data standardisation pipeline across DB tables:
    1. Canonical ISO-8601 Dates (YYYY-MM-DD)
    2. Canonical Currency (Numeric ₹, Crore, Paise)
    3. Canonical Category Taxonomy
    """
    res = run_standardization_pipeline(db_session=db)
    return {
        "status": "success",
        "message": "Data standardisation pipeline executed successfully.",
        "metrics": res
    }

@router.get("/preview")
def preview_standardization_rules():
    """Returns canonical taxonomy rules and date/currency formats."""
    return {
        "canonical_date_format": "ISO-8601 (YYYY-MM-DD)",
        "canonical_currency_format": "Float Rupees (₹) & Crores (Cr)",
        "category_taxonomy": [
            "Roads / Bridges / Transportation",
            "Drinking Water / Sanitation",
            "Education / Schools / Libraries",
            "Health / Medical Infrastructure",
            "Community Infrastructure / Halls",
            "Electricity / Renewable Energy",
            "Environment / Parks / Irrigation",
            "Other Public Infrastructure"
        ]
    }

