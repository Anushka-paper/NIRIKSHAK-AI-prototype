from difflib import SequenceMatcher

def compute_fuzzy_ratio(str1: str, str2: str) -> float:
    """Calculates SequenceMatcher similarity ratio."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

