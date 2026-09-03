"""
Exact and Deterministic Matcher.
Identifies deterministic pairs via exact official Work ID or identical composite keys.
"""

import pandas as pd
from .normalizer import normalize_work_id, normalize_text, normalize_mp_name, normalize_constituency

class ExactMatcher:
    """
    Executes high-confidence deterministic matching on candidate pairs.
    """

    def match(self, row_a: pd.Series, row_b: pd.Series, map_a: dict, map_b: dict) -> dict | None:
        """
        Evaluates deterministic match criteria.
        Returns match dict if deterministic criteria met, else None.
        """
        col_wid_a = map_a.get("work_id")
        col_wid_b = map_b.get("work_id")

        # 1. Exact Work ID Match
        if col_wid_a and col_wid_b:
            wid_a = normalize_work_id(row_a.get(col_wid_a))
            wid_b = normalize_work_id(row_b.get(col_wid_b))
            invalid_ids = {"", "NAN", "NONE", "NULL", "UNKNOWN", "0", "-"}

            if wid_a and wid_b and wid_a not in invalid_ids and wid_a == wid_b:
                return {
                    "is_match": True,
                    "match_method": "exact_work_id",
                    "match_score": 100.0,
                    "confidence_level": "HIGH",
                    "official_work_id": wid_a,
                    "field_scores": {"work_id": 100.0}
                }

        # 2. Exact Multi-Field Match (MP + Constituency + State + Normalized Description)
        col_mp_a = map_a.get("mp_name")
        col_mp_b = map_b.get("mp_name")
        col_const_a = map_a.get("constituency")
        col_const_b = map_b.get("constituency")
        col_desc_a = map_a.get("work_description")
        col_desc_b = map_b.get("work_description")

        if (col_mp_a and col_mp_b and col_const_a and col_const_b and col_desc_a and col_desc_b):
            mp_a = normalize_mp_name(row_a.get(col_mp_a))
            mp_b = normalize_mp_name(row_b.get(col_mp_b))
            const_a = normalize_constituency(row_a.get(col_const_a))
            const_b = normalize_constituency(row_b.get(col_const_b))
            desc_a = normalize_text(row_a.get(col_desc_a))
            desc_b = normalize_text(row_b.get(col_desc_b))

            if mp_a and mp_b and const_a and const_b and desc_a and desc_b:
                if mp_a == mp_b and const_a == const_b and desc_a == desc_b and len(desc_a) >= 15:
                    return {
                        "is_match": True,
                        "match_method": "exact_multi_field",
                        "match_score": 98.0,
                        "confidence_level": "HIGH",
                        "official_work_id": normalize_work_id(row_b.get(col_wid_b)) if col_wid_b else None,
                        "field_scores": {
                            "mp_name": 100.0,
                            "constituency": 100.0,
                            "work_description": 100.0
                        }
                    }

        return None

