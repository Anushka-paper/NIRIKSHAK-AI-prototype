"""
Review Queue Manager for Entity Resolution.
Stores medium-confidence pairs for human-in-the-loop audit and verification.
"""

import pandas as pd

class ReviewQueueManager:
    """
    Manages records requiring human review.
    """

    def __init__(self):
        self.queue = []

    def add_to_review(self, source_dataset: str, source_row_id: int | str,
                      candidate_dataset: str, candidate_row_id: int | str,
                      source_row: pd.Series, candidate_row: pd.Series,
                      map_a: dict, map_b: dict,
                      match_score: float, confidence_level: str, match_method: str,
                      field_scores: dict):
        """
        Adds candidate pair with side-by-side attributes to review queue.
        """
        item = {
            "source_dataset": source_dataset,
            "source_row_id": str(source_row_id),
            "candidate_dataset": candidate_dataset,
            "candidate_row_id": str(candidate_row_id),
            "source_work": str(source_row.get(map_a.get("work_description", ""), ""))[:150],
            "candidate_work": str(candidate_row.get(map_b.get("work_description", ""), ""))[:150],
            "source_mp": str(source_row.get(map_a.get("mp_name", ""), "")),
            "candidate_mp": str(candidate_row.get(map_b.get("mp_name", ""), "")),
            "source_constituency": str(source_row.get(map_a.get("constituency", ""), "")),
            "candidate_constituency": str(candidate_row.get(map_b.get("constituency", ""), "")),
            "source_state": str(source_row.get(map_a.get("state", ""), "")),
            "candidate_state": str(candidate_row.get(map_b.get("state", ""), "")),
            "source_amount": source_row.get(map_a.get("amount", ""), ""),
            "candidate_amount": candidate_row.get(map_b.get("amount", ""), ""),
            "match_score": round(match_score, 2),
            "confidence_level": confidence_level,
            "match_method": match_method,
            "decision": "pending",
            "review_status": "requires_human_review"
        }
        self.queue.append(item)

    def to_dataframe(self) -> pd.DataFrame:
        """Returns review queue as pandas DataFrame."""
        if not self.queue:
            return pd.DataFrame(columns=[
                "source_dataset", "source_row_id", "candidate_dataset", "candidate_row_id",
                "source_work", "candidate_work", "source_mp", "candidate_mp",
                "source_constituency", "candidate_constituency", "source_state", "candidate_state",
                "source_amount", "candidate_amount", "match_score", "confidence_level",
                "match_method", "decision", "review_status"
            ])
        return pd.DataFrame(self.queue)

