import pandas as pd

CATEGORY_MAP = {
    "ROAD": "ROADS_AND_BRIDGES",
    "BRIDGE": "ROADS_AND_BRIDGES",
    "PATHWAY": "ROADS_AND_BRIDGES",
    "WATER": "DRINKING_WATER",
    "DRINKING": "DRINKING_WATER",
    "EDUCATION": "EDUCATION",
    "SCHOOL": "EDUCATION",
    "HEALTH": "PUBLIC_HEALTH",
    "HOSPITAL": "PUBLIC_HEALTH",
    "SANITATION": "SANITATION",
    "TOILET": "SANITATION"
}

def map_category(val):
    if not isinstance(val, str) or not val.strip():
        return "OTHER_WORKS"
    v_upper = val.upper()
    for kw, cat in CATEGORY_MAP.items():
        if kw in v_upper:
            return cat
    return "OTHER_WORKS"

def standardise_categories(df, col_name="work_category"):
    if col_name in df.columns:
        df["raw_work_category"] = df[col_name].astype(str)
        df["canonical_work_category"] = df[col_name].apply(map_category)
    else:
        df["canonical_work_category"] = "OTHER_WORKS"
    return df
