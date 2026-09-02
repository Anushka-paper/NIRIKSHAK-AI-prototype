def validate_geography(df, house_name):
    missing_state = int(df["state"].isna().sum()) if "state" in df.columns else 0
    missing_const = 0
    if house_name == "LOK_SABHA" and "constituency" in df.columns:
        missing_const = int(df["constituency"].isna().sum())
    return missing_state, missing_const
