import difflib

def compute_string_similarity(str1, str2):
    if not str1 or not str2:
        return 0.0
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    if s1 == s2:
        return 1.0
    try:
        from rapidfuzz import fuzz
        return fuzz.token_set_ratio(s1, s2) / 100.0
    except ImportError:
        return round(difflib.SequenceMatcher(None, s1, s2).ratio(), 4)
