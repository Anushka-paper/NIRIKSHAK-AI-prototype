import pandas as pd

STATUS_MAP = {
    "APPROVED": "SANCTIONED",
    "SANCTIONED": "SANCTIONED",
    "COMPLETED": "COMPLETED",
    "IN PROGRESS": "IN_PROGRESS",
    "ONGOING": "IN_PROGRESS",
    "PAID": "PAYMENT_SUCCESSFUL",
    "SUCCESSFUL": "PAYMENT_SUCCESSFUL",
    "PENDING": "PAYMENT_PENDING"
}

def map_status(val):
    if not isinstance(val, str) or not val.strip():
        return "UNKNOWN"
    v_upper = val.strip().upper()
    return STATUS_MAP.get(v_upper, "OTHER_STATUS")

def standardise_statuses(df):
    if "work_status" in df.columns:
        df["raw_work_status"] = df["work_status"].astype(str)
        df["canonical_work_status"] = df["work_status"].apply(map_status)
        
    if "payment_status" in df.columns:
        df["raw_payment_status"] = df["payment_status"].astype(str)
        df["canonical_payment_status"] = df["payment_status"].apply(map_status)
        
    return df
