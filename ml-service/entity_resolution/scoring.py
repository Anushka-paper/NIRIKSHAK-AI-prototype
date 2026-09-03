"""
Multi-Field Weighted Scoring Engine.
Dynamically normalizes weights based on which fields actually exist in the two compared records.
"""

from .config import DEFAULT_FIELD_WEIGHTS

class ScoringEngine:
    """
    Computes a composite multi-field similarity score (0.0 - 100.0)
    with dynamic weight normalization.
    """

    def __init__(self, weights: dict = None):
        self.weights = weights or DEFAULT_FIELD_WEIGHTS

    def compute_composite_score(self, field_scores: dict[str, float]) -> tuple[float, dict[str, float]]:
        """
        Calculates normalized weighted score based only on present fields.
        Returns (composite_score, normalized_weights_used).
        """
        if not field_scores:
            return 0.0, {}

        # 1. Collect applicable weights
        applicable_weights = {}
        for field, score in field_scores.items():
            if field in self.weights:
                applicable_weights[field] = self.weights[field]
            else:
                applicable_weights[field] = 0.05  # Default fallback weight for extra fields

        total_weight = sum(applicable_weights.values())
        if total_weight <= 0:
            return 0.0, {}

        # 2. Normalize weights to sum to 1.0
        normalized_weights = {f: w / total_weight for f, w in applicable_weights.items()}

        # 3. Compute weighted average
        weighted_sum = sum(field_scores[f] * normalized_weights[f] for f in field_scores)

        # Critical heuristic: if work_description is present and below 40, penalize heavily
        if "work_description" in field_scores and field_scores["work_description"] < 40.0:
            weighted_sum = weighted_sum * 0.60

        # Critical heuristic: if state or constituency is mismatched (< 50), penalize
        if "state" in field_scores and field_scores["state"] < 50.0:
            weighted_sum = weighted_sum * 0.50

        composite_score = max(0.0, min(100.0, round(weighted_sum, 2)))
        return composite_score, normalized_weights

