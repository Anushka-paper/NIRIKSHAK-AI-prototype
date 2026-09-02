import pandas as pd

def profile_nulls(df, req_cols):
    profile = {}
    for col in df.columns:
        total = len(df)
        null_c = int(df[col].isna().sum())
        non_null_c = total - null_c
        pct = round((null_c / total) * 100.0, 2) if total > 0 else 0.0
        
        classification = "OPTIONAL"
        if col in req_cols or col in ["work", "state", "source_house"]:
            classification = "REQUIRED"
        elif "date" in col or "amount" in col:
            classification = "CONDITIONALLY_REQUIRED"
            
        profile[col] = {
            "total_records": total,
            "null_count": null_c,
            "non_null_count": non_null_c,
            "null_percentage": pct,
            "classification": classification
        }
    return profile
