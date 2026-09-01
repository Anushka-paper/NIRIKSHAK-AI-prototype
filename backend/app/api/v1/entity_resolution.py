import os
import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from db.session import get_db
from ingestion.entity_resolution.pipeline import run_entity_resolution_pipeline
from ingestion.entity_resolution.entity_resolver import WorkIDResolver, MPNameResolver, VendorNameResolver

router = APIRouter(prefix="/entity-resolution", tags=["Entity Resolution"])

@router.post("/run")
def trigger_entity_resolution(db: Session = Depends(get_db)):
    """
    Triggers Entity Resolution across all DB entities:
    1. Composite Work ID Extraction & Canonical Parsing
    2. MP Name Normalization & Alias Mapping
    3. Vendor Name Normalization & Master Mapping
    """
    stats = run_entity_resolution_pipeline(db_session=db)
    return {
        "status": "success",
        "message": "Entity Resolution pipeline executed successfully.",
        "metrics": stats
    }

@router.get("/parse-work-id")
def parse_work_id_preview(raw_work_id: str = "MPLADS/2023/105635 - Construction of Road"):
    """Tests canonical Work ID parser on any raw composite string."""
    canonical, raw = WorkIDResolver.parse_canonical_work_id(raw_work_id)
    return {
        "raw_work_id": raw,
        "canonical_work_id": canonical
    }

@router.get("/resolve-mp")
def resolve_mp_preview(raw_mp_name: str = "Shri Narendra Modi"):
    """Tests MP entity resolution and honorific stripping."""
    norm = MPNameResolver.normalize_mp_name(raw_mp_name)
    return {
        "raw_mp_name": raw_mp_name,
        "normalized_mp_name": norm
    }

@router.get("/resolve-vendor")
def resolve_vendor_preview(raw_vendor_name: str = "M/s ABC Construction Pvt. Ltd."):
    """Tests Vendor entity resolution and company suffix standardization."""
    norm = VendorNameResolver.normalize_vendor_name(raw_vendor_name)
    return {
        "raw_vendor_name": raw_vendor_name,
        "normalized_vendor_name": norm
    }

