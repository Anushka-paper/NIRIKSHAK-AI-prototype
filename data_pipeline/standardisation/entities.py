import re
import pandas as pd

HONORIFICS_PATTERN = r"^(SHRI|SMT|DR\.?|PROF\.?|ADV\.?|HONABLE|HON'BLE)\s+"

def clean_mp_name(val):
    if not isinstance(val, str) or not val.strip():
        return "UNKNOWN_MP"
    v = val.strip().upper()
    v = re.sub(HONORIFICS_PATTERN, '', v)
    v = re.sub(HONORIFICS_PATTERN, '', v) # run twice if Shri Dr
    v = ' '.join(v.split())
    return v

def standardise_entities(df):
    mp_col = None
    for c in ["honble_members_of_parliaments", "honble_members_of_parliament"]:
        if c in df.columns:
            mp_col = c
            break
            
    if mp_col:
        df["raw_mp_name"] = df[mp_col].astype(str)
        df["canonical_mp_name"] = df[mp_col].apply(clean_mp_name)
        df["canonical_mp_id"] = "MP_" + df["source_house"].astype(str) + "_" + df["canonical_mp_name"].str.replace(r'[^A-Z0-9]', '_', regex=True)

    if "vendor_name" in df.columns:
        df["raw_vendor_name"] = df["vendor_name"].astype(str)
        df["canonical_vendor_name"] = df["vendor_name"].fillna("").astype(str).str.strip().str.upper()
        df["canonical_vendor_id"] = "VENDOR_" + df["canonical_vendor_name"].str.replace(r'[^A-Z0-9]', '_', regex=True)

    return df
