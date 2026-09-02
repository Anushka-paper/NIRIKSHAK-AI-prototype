def validate_work_ids(df):
    if "work_id" not in df.columns:
        return 0, 0
    s = df["work_id"].dropna().astype(str)
    blank_count = (s.str.strip() == "").sum()
    malformed_count = (~s.str.startswith("WS/")).sum()
    return blank_count, malformed_count
