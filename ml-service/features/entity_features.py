"""
Entity, Provenance, and Lineage Feature Generator.
"""

import pandas as pd
import numpy as np

def compute_entity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes entity-level features, flags, and provenance indicators.
    """
    df = df.copy()

    # Existence flags
    df["has_official_work_id"] = df["official_work_id"].notna() & (df["official_work_id"].astype(str).str.strip() != "") & (df["official_work_id"].astype(str).str.lower() != "none")
    df["has_official_work_id"] = df["has_official_work_id"].astype(int)

    df["has_canonical_work_id"] = df["canonical_work_id"].notna() & (df["canonical_work_id"].astype(str).str.strip() != "")
    df["has_canonical_work_id"] = df["has_canonical_work_id"].astype(int)

    # ER flags
    df["entity_resolution_score"] = pd.to_numeric(df.get("er_match_score", 100.0), errors="coerce").fillna(100.0)
    df["entity_resolution_confidence"] = df.get("er_confidence", "HIGH").fillna("HIGH")
    df["entity_resolution_method"] = df.get("er_method", "exact").fillna("exact")
    
    df["entity_resolution_uncertain"] = (
        (df["entity_resolution_score"] < 85.0) | 
        (df["entity_resolution_confidence"].isin(["LOW", "REVIEW", "NONE"]))
    ).astype(int)

    df["entity_resolution_review_required"] = (
        df["entity_resolution_confidence"] == "REVIEW"
    ).astype(int)

    return df

