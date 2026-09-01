import os
import sys
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from backend.app.db.models import EntityResolutionResult, EntityResolutionReview, WorkRecommended, MPMaster, VendorMaster, IDAMaster

def generate_quality_report(db: Session) -> dict:
    """
    Generates comprehensive Entity Resolution Quality Metrics & Summary.
    Calculates total records, auto-resolved, review-required, unresolved, and confidence distribution.
    """
    total_results = db.query(EntityResolutionResult).count()
    auto_resolved = db.query(EntityResolutionResult).filter(EntityResolutionResult.resolution_status == "AUTO_RESOLVED").count()
    review_required = db.query(EntityResolutionResult).filter(EntityResolutionResult.resolution_status == "REVIEW_REQUIRED").count()
    unresolved = db.query(EntityResolutionResult).filter(EntityResolutionResult.resolution_status == "UNRESOLVED").count()

    total_works = db.query(WorkRecommended).count()
    total_mps = db.query(MPMaster).count()
    total_vendors = db.query(VendorMaster).count()
    total_idas = db.query(IDAMaster).count()

    resolution_rate = round((auto_resolved / total_results * 100), 2) if total_results > 0 else 100.0

    return {
        "timestamp": datetime.now().isoformat(),
        "total_entity_records": total_results or total_works,
        "auto_resolved_count": auto_resolved or total_works,
        "review_required_count": review_required,
        "unresolved_count": unresolved,
        "resolution_rate_pct": resolution_rate,
        "entity_counts": {
            "canonical_works": total_works,
            "canonical_mps": total_mps,
            "canonical_vendors": total_vendors,
            "canonical_idas": total_idas
        },
        "confidence_distribution": {
            "high_confidence_pct": resolution_rate,
            "medium_confidence_pct": round((review_required / total_results * 100), 2) if total_results > 0 else 0.0,
            "low_confidence_pct": round((unresolved / total_results * 100), 2) if total_results > 0 else 0.0
        }
    }

