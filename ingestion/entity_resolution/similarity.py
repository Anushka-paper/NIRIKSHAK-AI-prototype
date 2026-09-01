from difflib import SequenceMatcher

class SimilarityEngine:
    """
    Multi-metric String Similarity Calculator.
    Calculates SequenceMatcher ratio, Token-Sort ratio, and Partial Token ratio.
    """

    @staticmethod
    def lev_ratio(str1: str, str2: str) -> float:
        """Basic sequence matching ratio."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()

    @staticmethod
    def token_sort_ratio(str1: str, str2: str) -> float:
        """Token sort similarity ratio (handles word reordering)."""
        if not str1 or not str2:
            return 0.0
        sorted_1 = " ".join(sorted(str1.split()))
        sorted_2 = " ".join(sorted(str2.split()))
        return SequenceMatcher(None, sorted_1, sorted_2).ratio()

    @classmethod
    def composite_string_similarity(cls, str1: str, str2: str) -> float:
        """Weighted blend of basic ratio and token sort ratio."""
        if str1 == str2:
            return 1.0
        r_basic = cls.lev_ratio(str1, str2)
        r_sort = cls.token_sort_ratio(str1, str2)
        return round(0.4 * r_basic + 0.6 * r_sort, 4)

