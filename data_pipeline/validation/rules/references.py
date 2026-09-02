def validate_work_references(df_exp, df_works):
    if "work_id" not in df_exp.columns or "work_id" not in df_works.columns:
        return 0
    exp_ids = set(df_exp["work_id"].dropna())
    work_ids = set(df_works["work_id"].dropna())
    unmatched = len(exp_ids - work_ids)
    return unmatched
