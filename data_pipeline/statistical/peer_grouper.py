import numpy as np
import pandas as pd
from data_pipeline.statistical.config import SIZE_TIER_CUTOFFS

def assign_peer_groups(df_work):
    df = df_work.copy()
    
    amt = pd.to_numeric(df.get("sanctioned_amount_inr", df.get("recommended_amount_inr", pd.Series(0.0, index=df.index))), errors="coerce").fillna(0.0)
    
    conditions = [
        amt <= SIZE_TIER_CUTOFFS["SMALL"],
        (amt > SIZE_TIER_CUTOFFS["SMALL"]) & (amt <= SIZE_TIER_CUTOFFS["MEDIUM"])
    ]
    choices = ["SMALL", "MEDIUM"]
    df["project_size_tier"] = np.select(conditions, choices, default="LARGE")
    
    cat = df.get("canonical_work_category", pd.Series("OTHER_WORKS", index=df.index)).fillna("OTHER_WORKS").astype(str)
    state = df.get("canonical_state", pd.Series("UNKNOWN", index=df.index)).fillna("UNKNOWN").astype(str)
    tier = df["project_size_tier"].astype(str)
    
    df["peer_group_key"] = cat + "::" + state + "::" + tier
    return df
