def validate_schema(df, req_cols):
    missing_req = []
    for req in req_cols:
        req_clean = req.replace("₹", "").strip("_")
        found = any(req_clean in c.replace("₹", "").strip("_") for c in df.columns)
        if not found:
            missing_req.append(req)
    return missing_req
