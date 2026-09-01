import pandas as pd

def standardise_geography(df, house_name):
    if "state" in df.columns:
        df["raw_state"] = df["state"].astype(str)
        df["canonical_state"] = df["state"].fillna("").astype(str).str.strip().str.upper()
        df["canonical_state_id"] = "STATE_" + df["canonical_state"].str.replace(r'[^A-Z0-9]', '_', regex=True)
    
    if "constituency" in df.columns:
        df["raw_constituency"] = df["constituency"].astype(str)
        df["canonical_constituency"] = df["constituency"].fillna("").astype(str).str.strip().str.upper()
        df["canonical_constituency_id"] = "CONST_" + df["canonical_constituency"].str.replace(r'[^A-Z0-9]', '_', regex=True)
    elif "elected/nominated" in df.columns:
        df["raw_constituency"] = df["elected/nominated"].astype(str)
        df["canonical_constituency"] = df["elected/nominated"].fillna("").astype(str).str.strip().str.upper()
        df["canonical_constituency_id"] = "NOM_" + df["canonical_constituency"].str.replace(r'[^A-Z0-9]', '_', regex=True)

    if "ida" in df.columns:
        df["raw_ida"] = df["ida"].astype(str)
        df["canonical_ida"] = df["ida"].fillna("").astype(str).str.strip().str.upper()
        df["canonical_authority_id"] = "IDA_" + df["canonical_ida"].str.replace(r'[^A-Z0-9]', '_', regex=True)

    return df
