"""
Confidence Classifier for Entity Resolution.
Classifies scores into HIGH (MATCH), MEDIUM (REVIEW), or LOW (NO_MATCH).
"""

from .config import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD

class ConfidenceClassifier:
    """
    Classifies candidate match evaluations into 3-way decisions: MATCH, REVIEW, or NO_MATCH.
    """

    def __init__(self, high_threshold: float = HIGH_CONFIDENCE_THRESHOLD, 
                 medium_threshold: float = MEDIUM_CONFIDENCE_THRESHOLD):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

    def classify(self, score: float, match_method: str = "fuzzy") -> tuple[str, str]:
        """
        Returns (confidence_level, decision).
        confidence_level: 'HIGH', 'MEDIUM', 'LOW'
        decision: 'MATCH', 'REVIEW', 'NO_MATCH'
        """
        # Deterministic methods get automatic HIGH / MATCH
        if match_method in {"exact_work_id", "exact_multi_field"}:
            return "HIGH", "MATCH"

        if score >= self.high_threshold:
            return "HIGH", "MATCH"
        elif score >= self.medium_threshold:
            return "MEDIUM", "REVIEW"
        else:
            return "LOW", "NO_MATCH"

