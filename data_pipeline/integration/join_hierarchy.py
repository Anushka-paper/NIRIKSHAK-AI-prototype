import pandas as pd

def match_by_work_id(df_left, df_right, left_key="canonical_work_id", right_key="canonical_work_id"):
    if df_left.empty or df_right.empty:
        return df_left
    merged = df_left.merge(df_right, on=[left_key], how="outer", suffixes=("", "_right"))
    merged["match_method"] = "WORK_ID"
    merged["match_confidence"] = "HIGH"
    return merged
