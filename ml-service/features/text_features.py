"""
Text Complexity and Syntactic Feature Generator for Work Descriptions.
Preserves original text untouched and derives numerical complexity signals.
"""

import string
import pandas as pd
import numpy as np

def compute_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives character counts, word counts, syntactic ratios, and brevity flags.
    """
    df = df.copy()

    desc_col = df["work_description"].fillna("").astype(str)

    char_counts = desc_col.str.len()
    word_counts = desc_col.apply(lambda s: len(s.split()) if s.strip() else 0)
    
    df["work_description_length"] = char_counts
    df["work_description_word_count"] = word_counts
    df["has_work_description"] = (word_counts > 0).astype(int)
    df["work_description_missing"] = (word_counts == 0).astype(int)

    # Unique words & average word length
    def calc_text_stats(s: str):
        if not s.strip():
            return 0, 0.0, 0.0, 0.0, 0.0
        words = s.split()
        unique_w = len(set(words))
        avg_w_len = sum(len(w) for w in words) / max(1, len(words))
        
        n_chars = len(s)
        n_upper = sum(1 for c in s if c.isupper())
        n_digit = sum(1 for c in s if c.isdigit())
        n_punct = sum(1 for c in s if c in string.punctuation)

        return (
            unique_w,
            round(avg_w_len, 2),
            round(n_upper / n_chars, 3),
            round(n_digit / n_chars, 3),
            round(n_punct / n_chars, 3),
        )

    stats = [calc_text_stats(t) for t in desc_col]
    df["unique_word_count"] = [s[0] for s in stats]
    df["average_word_length"] = [s[1] for s in stats]
    df["uppercase_ratio"] = [s[2] for s in stats]
    df["digit_ratio"] = [s[3] for s in stats]
    df["punctuation_ratio"] = [s[4] for s in stats]

    # Flags
    df["very_short_text_flag"] = ((word_counts > 0) & (word_counts < 4)).astype(int)
    df["very_long_text_flag"] = (word_counts > 40).astype(int)

    return df

