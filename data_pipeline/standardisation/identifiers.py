import pandas as pd

def get_series(df, col):
    if col in df.columns:
        return df[col].fillna("").astype(str)
    return pd.Series("", index=df.index)

def standardise_identifiers(df):
    house_s = get_series(df, "source_house")
    state_s = get_series(df, "canonical_state")
    mp_s = get_series(df, "canonical_mp_name")
    work_s = get_series(df, "work")
    date_s = get_series(df, "recommended_date")

    key_s = house_s + "_" + state_s + "_" + mp_s + "_" + work_s + "_" + date_s
    fast_hashes = pd.util.hash_pandas_object(key_s, index=False).astype(str)

    if "work_id" in df.columns:
        existing_wids = df["work_id"].fillna("").astype(str).str.strip()
        has_wid = existing_wids != ""
        
        df["canonical_work_id"] = existing_wids
        
        missing_mask = ~has_wid
        if missing_mask.sum() > 0:
            df.loc[missing_mask, "canonical_work_id"] = "WORK_HASH_" + fast_hashes[missing_mask]
    else:
        df["canonical_work_id"] = "WORK_HASH_" + fast_hashes
        
    # Financial Year extraction
    if "recommended_date" in df.columns:
        dates = pd.to_datetime(df["recommended_date"], errors='coerce')
        years = dates.dt.year
        df["financial_year"] = years.apply(lambda y: f"{int(y)}-{int(y)+1}" if pd.notna(y) else "UNKNOWN_FY")
    else:
        df["financial_year"] = "UNKNOWN_FY"
        
    return df
