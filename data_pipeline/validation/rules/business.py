def validate_business_rules(df):
    if "work_status" in df.columns and "completion_date" in df.columns:
        completed_mask = df["work_status"].str.upper() == "COMPLETED"
        missing_comp = int((completed_mask & df["completion_date"].isna()).sum())
        return missing_comp
    return 0
