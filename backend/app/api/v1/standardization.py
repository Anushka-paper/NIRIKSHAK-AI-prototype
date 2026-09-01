import os
import sys
from fastapi import APIRouter
from data_pipeline.standardisation.pipeline import run_standardisation_pipeline

router = APIRouter(prefix="/standardization", tags=["Data Standardization"])

@router.post("/run")
def trigger_data_standardization():
    """
    Triggers canonical data standardisation pipeline across datasets:
    1. Canonical ISO-8601 Dates (YYYY-MM-DD)
    2. Canonical Currency (Numeric ₹)
    3. Canonical Category Taxonomy
    """
    run_standardisation_pipeline()
    return {
        "status": "success",
        "message": "Data standardisation pipeline executed successfully."
    }

@router.get("/preview")
def preview_standardization_rules():
    """Returns canonical taxonomy rules and date/currency formats."""
    return {
        "canonical_date_format": "ISO-8601 (YYYY-MM-DD)",
        "canonical_currency_format": "Float Rupees (₹)",
        "category_taxonomy": [
            "ROADS_AND_BRIDGES",
            "DRINKING_WATER",
            "EDUCATION",
            "PUBLIC_HEALTH",
            "SANITATION",
            "OTHER_WORKS"
        ]
    }
