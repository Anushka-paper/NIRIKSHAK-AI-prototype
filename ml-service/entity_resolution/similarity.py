"""
Multi-Field Similarity Metrics for Entity Resolution.
Calculates text similarity, amount tolerance ratio, and chronological date plausibility.
"""

import math
from difflib import SequenceMatcher
from datetime import datetime

try:
    import rapidfuzz
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

def calculate_string_similarity(str1: str, str2: str) -> float:
    """
    Computes token and string similarity score (0.0 to 100.0).
    Uses RapidFuzz token_sort_ratio if available, otherwise optimized difflib token similarity.
    """
    if not str1 or not str2:
        return 0.0

    s1 = str1.strip()
    s2 = str2.strip()
    if s1 == s2:
        return 100.0

    if HAS_RAPIDFUZZ:
        return float(fuzz.token_sort_ratio(s1, s2))

    # Difflib Fallback with token sorting
    tokens1 = " ".join(sorted(s1.split()))
    tokens2 = " ".join(sorted(s2.split()))
    if tokens1 == tokens2:
        return 100.0

    ratio = SequenceMatcher(None, tokens1, tokens2).ratio() * 100.0
    return round(ratio, 2)

def calculate_amount_similarity(amt1: float | None, amt2: float | None, tolerance_pct: float = 0.15) -> float:
    """
    Calculates amount similarity score (0.0 to 100.0).
    Tolerates legitimate revisions between recommendation, sanction, and expenditure.
    """
    if amt1 is None or amt2 is None:
        return 0.0

    if amt1 <= 0 or amt2 <= 0:
        return 100.0 if amt1 == amt2 else 0.0

    diff = abs(amt1 - amt2)
    max_amt = max(amt1, amt2)

    # Exact or minimal rounding difference (<= Rs. 100)
    if diff <= 100.0:
        return 100.0

    rel_diff = diff / max_amt
    if rel_diff <= tolerance_pct:
        # Scale between 100.0 and 80.0 within tolerance
        return round(100.0 - (rel_diff / tolerance_pct) * 20.0, 2)

    # Exponential decay above tolerance
    excess = rel_diff - tolerance_pct
    score = max(0.0, 80.0 * math.exp(-2.0 * excess))
    return round(score, 2)

def calculate_date_compatibility(date1_str: str | None, date2_str: str | None, is_chronological: bool = True) -> float:
    """
    Checks chronological plausibility or temporal closeness between two dates.
    For lifecycle (e.g. rec_date <= sanc_date), returns 100.0 if chronological order holds.
    """
    if not date1_str or not date2_str:
        return 50.0  # Neutral if one date missing

    try:
        d1 = datetime.strptime(str(date1_str)[:10], "%Y-%m-%d")
        d2 = datetime.strptime(str(date2_str)[:10], "%Y-%m-%d")
    except Exception:
        return 50.0

    days_diff = (d2 - d1).days

    if is_chronological:
        # e.g. date1 is recommendation, date2 is sanction
        if days_diff >= 0:
            # Within 3 years is completely normal for public works
            if days_diff <= 1095:
                return 100.0
            else:
                return 80.0
        else:
            # Chronology inverted (sanction before recommendation) - penalize
            return 30.0
    else:
        # Closeness check
        abs_days = abs(days_diff)
        if abs_days <= 30:
            return 100.0
        elif abs_days <= 180:
            return 80.0
        elif abs_days <= 365:
            return 60.0
        else:
            return 40.0

