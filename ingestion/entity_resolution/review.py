import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "backend/app"))

from backend.app.db.models import EntityResolutionReview, MPAlias, VendorAlias, IDAAlias

class ReviewQueueManager:
    """
    Manual Review Queue & Alias Learning Engine.
    Handles queueing ambiguous matches and learning new aliases from confirmed reviewer decisions.
    """

    @staticmethod
    def queue_for_review(db: Session, 
                         entity_type: str, 
                         source_value: str, 
                         candidate_id: str, 
                         candidate_name: str, 
                         confidence_score: float, 
                         reason: str = "Medium confidence threshold match"):
        """Queues an ambiguous match for human review."""
        review_entry = EntityResolutionReview(
            entity_type=entity_type,
            source_value=source_value,
            candidate_id=str(candidate_id),
            candidate_name=candidate_name,
            confidence_score=confidence_score,
            reason=reason,
            status="REVIEW_REQUIRED"
        )
        db.add(review_entry)
        db.flush()
        return review_entry.review_id

    @staticmethod
    def process_review_decision(db: Session, 
                                review_id: int, 
                                decision: str, 
                                reviewer: str = "human_auditor", 
                                notes: str = None) -> bool:
        """
        Processes human reviewer decision (CONFIRMED / REJECTED).
        If CONFIRMED, automatically learns the alias into master alias table!
        """
        review = db.query(EntityResolutionReview).filter(EntityResolutionReview.review_id == review_id).first()
        if not review:
            return False

        review.status = decision.upper()
        review.reviewer = reviewer
        review.reviewed_at = datetime.now()
        review.final_decision = decision.upper()

        # Alias Learning Loop: Store confirmed alias for zero-cost future lookups!
        if decision.upper() == "CONFIRMED":
            if review.entity_type == "mp":
                alias = MPAlias(
                    mp_id=int(review.candidate_id),
                    raw_name=review.source_value,
                    normalized_name=review.source_value.lower(),
                    confidence_score=1.0,
                    matching_method="human_confirmed",
                    verified=True
                )
                db.add(alias)
            elif review.entity_type == "vendor":
                alias = VendorAlias(
                    vendor_id=int(review.candidate_id),
                    raw_name=review.source_value,
                    normalized_name=review.source_value.lower(),
                    match_confidence=1.0,
                    matching_method="human_confirmed",
                    verified=True
                )
                db.add(alias)

        db.commit()
        return True

