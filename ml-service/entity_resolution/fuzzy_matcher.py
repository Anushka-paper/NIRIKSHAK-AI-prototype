"""
Fuzzy Multi-Field Matcher.
Computes normalized similarity across text, names, descriptions, amounts, and dates.
"""

import pandas as pd
from .normalizer import normalize_text, normalize_mp_name, normalize_constituency, normalize_amount_to_float
from .similarity import calculate_string_similarity, calculate_amount_similarity, calculate_date_compatibility

class FuzzyMatcher:
    """
    Evaluates candidate record pairs across multiple fields using fuzzy string matching,
    monetary tolerance, and date plausibility.
    """

    def evaluate_pair(self, row_a: pd.Series, row_b: pd.Series, map_a: dict, map_b: dict) -> dict:
        """
        Computes itemized field similarities between two records.
        Returns dict mapping field_name -> similarity_score (0-100).
        """
        field_scores = {}

        # 1. Work Description Similarity
        col_desc_a = map_a.get("work_description")
        col_desc_b = map_b.get("work_description")
        if col_desc_a and col_desc_b:
            desc_a = normalize_text(row_a.get(col_desc_a))
            desc_b = normalize_text(row_b.get(col_desc_b))
            field_scores["work_description"] = calculate_string_similarity(desc_a, desc_b)

        # 2. MP Name Similarity
        col_mp_a = map_a.get("mp_name")
        col_mp_b = map_b.get("mp_name")
        if col_mp_a and col_mp_b:
            mp_a = normalize_mp_name(row_a.get(col_mp_a))
            mp_b = normalize_mp_name(row_b.get(col_mp_b))
            field_scores["mp_name"] = calculate_string_similarity(mp_a, mp_b)

        # 3. Constituency Similarity
        col_const_a = map_a.get("constituency")
        col_const_b = map_b.get("constituency")
        if col_const_a and col_const_b:
            const_a = normalize_constituency(row_a.get(col_const_a))
            const_b = normalize_constituency(row_b.get(col_const_b))
            field_scores["constituency"] = calculate_string_similarity(const_a, const_b)

        # 4. State Similarity
        col_st_a = map_a.get("state")
        col_st_b = map_b.get("state")
        if col_st_a and col_st_b:
            st_a = normalize_text(row_a.get(col_st_a))
            st_b = normalize_text(row_b.get(col_st_b))
            field_scores["state"] = calculate_string_similarity(st_a, st_b)

        # 5. Amount Similarity
        col_amt_a = map_a.get("amount")
        col_amt_b = map_b.get("amount")
        if col_amt_a and col_amt_b:
            amt_a = normalize_amount_to_float(row_a.get(col_amt_a))
            amt_b = normalize_amount_to_float(row_b.get(col_amt_b))
            field_scores["amount"] = calculate_amount_similarity(amt_a, amt_b)

        # 6. Date Compatibility
        # Find dates present in row_a and row_b
        date_a = next((row_a.get(map_a[k]) for k in ["recommendation_date", "sanction_date", "date"] if k in map_a), None)
        date_b = next((row_b.get(map_b[k]) for k in ["sanction_date", "completion_date", "expenditure_date", "date"] if k in map_b), None)
        if date_a and date_b:
            field_scores["date"] = calculate_date_compatibility(str(date_a), str(date_b))

        # 7. IDA Agency Similarity
        col_ida_a = map_a.get("ida_agency")
        col_ida_b = map_b.get("ida_agency")
        if col_ida_a and col_ida_b:
            ida_a = normalize_text(row_a.get(col_ida_a))
            ida_b = normalize_text(row_b.get(col_ida_b))
            field_scores["ida_agency"] = calculate_string_similarity(ida_a, ida_b)

        return field_scores

