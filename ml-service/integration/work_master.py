"""
Unified Dataset Integration for NIRIKSHAK-AI.
Merges lifecycle stages (recommended, sanctioned, expenditure, completed)
using canonical_work_id and official_work_id from Entity Resolution output.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("NIRIKSHAK-INTEGRATION")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def build_unified_work_master(parliament: str = "lok_sabha",
                               std_dir: Optional[Path] = None,
                               er_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Builds the Unified Work Master and Transaction Tables for a parliament.
    Returns:
        (work_master_df, transaction_master_df)
    """
    std_path = std_dir or (BASE_DIR / "data" / "standardized" / parliament)
    er_path = er_dir or (BASE_DIR / "data" / "entity_resolution" / parliament)

    # 1. Load ER matches to build canonical work index
    matches_csv = er_path / "entity_resolution_matches.csv"
    canonical_lookup = {}
    if matches_csv.exists():
        try:
            m_df = pd.read_csv(matches_csv)
            for _, r in m_df.iterrows():
                cid = str(r.get("canonical_work_id", "")).strip()
                s_ds = str(r.get("source_dataset", "")).strip().lower()
                s_row = r.get("source_row_id")
                m_ds = str(r.get("matched_dataset", "")).strip().lower()
                m_row = r.get("matched_row_id")
                off_id = str(r.get("official_work_id", "")).strip()
                score = r.get("match_score", 100.0)
                conf = str(r.get("confidence_level", "HIGH")).strip()
                meth = str(r.get("match_method", "exact")).strip()

                if cid:
                    if pd.notna(s_row):
                        canonical_lookup[(s_ds, int(s_row))] = (cid, off_id, score, conf, meth)
                    if pd.notna(m_row):
                        canonical_lookup[(m_ds, int(m_row))] = (cid, off_id, score, conf, meth)
        except Exception as e:
            logger.warning(f"Failed to parse ER matches: {e}")

    # 2. Discover standardized lifecycle datasets
    def find_csv(keyword: str):
        matches = list(std_path.glob(f"*{keyword}*_standardized.csv"))
        return matches[0] if matches else None

    rec_csv = find_csv("recommended")
    sanc_csv = find_csv("sanctioned")
    exp_csv = find_csv("expenditure")
    comp_csv = find_csv("completed")

    rec_df = pd.read_csv(rec_csv, low_memory=False) if rec_csv and rec_csv.exists() else pd.DataFrame()
    sanc_df = pd.read_csv(sanc_csv, low_memory=False) if sanc_csv and sanc_csv.exists() else pd.DataFrame()
    exp_df = pd.read_csv(exp_csv, low_memory=False) if exp_csv and exp_csv.exists() else pd.DataFrame()
    comp_df = pd.read_csv(comp_csv, low_memory=False) if comp_csv and comp_csv.exists() else pd.DataFrame()

    logger.info(f"Loaded datasets for [{parliament}]: Rec={len(rec_df)}, Sanc={len(sanc_df)}, Exp={len(exp_df)}, Comp={len(comp_df)}")

    # 3. Process Transaction-Level Data (Expenditure)
    transactions = []
    if not exp_df.empty:
        for idx, row in exp_df.iterrows():
            cid, off_id, score, conf, meth = canonical_lookup.get(("expenditure", idx), ("", "", np.nan, "NONE", "unmatched"))
            row_work_id = str(row.get("work_id", "")).strip()
            if not off_id and row_work_id and row_work_id != "nan":
                off_id = row_work_id
            
            amt = pd.to_numeric(row.get("expenditure_amount", 0.0), errors="coerce") or 0.0
            date_val = row.get("expenditure_date", row.get("transaction_date", None))

            transactions.append({
                "transaction_id": f"TX_{parliament[:2].upper()}_{idx+1:06d}",
                "canonical_work_id": cid or (f"CW_{parliament[:2].upper()}_EXP_{idx+1:06d}"),
                "official_work_id": off_id if off_id and off_id != "nan" else None,
                "parliament": parliament,
                "source_dataset": "expenditure",
                "source_row_id": idx,
                "vendor_name": str(row.get("vendor_name", "")).strip() if pd.notna(row.get("vendor_name")) else None,
                "ida_agency": str(row.get("ida_agency", "")).strip() if pd.notna(row.get("ida_agency")) else None,
                "work_status": str(row.get("work_status", "")).strip() if pd.notna(row.get("work_status")) else None,
                "transaction_amount": float(amt),
                "transaction_date": str(date_val) if pd.notna(date_val) else None,
                "state": str(row.get("state", "")).strip() if pd.notna(row.get("state")) else None,
                "constituency": str(row.get("constituency", "")).strip() if pd.notna(row.get("constituency")) else None,
                "mp_name": str(row.get("mp_name", "")).strip() if pd.notna(row.get("mp_name")) else None,
            })

    transaction_df = pd.DataFrame(transactions)

    # 4. Integrate into Unified Work Master
    # Use Sanctioned as primary base if present, else Recommended, else Completed
    master_records = {}

    def get_or_create_master_record(cid, off_id, state, const, mp, cat, desc):
        key = cid if cid else (off_id if off_id else f"{state}_{const}_{mp}_{desc[:30]}")
        if key not in master_records:
            master_records[key] = {
                "canonical_work_id": cid,
                "official_work_id": off_id if off_id and off_id != "nan" else None,
                "parliament": parliament,
                "state": state,
                "constituency": const,
                "mp_name": mp,
                "work_category": cat,
                "work_description": desc,
                "recommended_date": None,
                "recommended_amount": np.nan,
                "sanction_date": None,
                "sanctioned_amount": np.nan,
                "completion_date": None,
                "completion_amount": np.nan,
                "expenditure_amount": 0.0,
                "expenditure_transaction_count": 0,
                "first_expenditure_date": None,
                "last_expenditure_date": None,
                "vendor_name": None,
                "ida_agency": None,
                "work_status": None,
                "er_match_score": 100.0 if cid else np.nan,
                "er_confidence": "HIGH" if cid else "NONE",
                "er_method": "exact" if cid else "unmatched",
                "has_recommendation": 0,
                "has_sanction": 0,
                "has_expenditure": 0,
                "has_completion": 0,
            }
        return master_records[key]

    # A. Ingest Sanctioned
    if not sanc_df.empty:
        for idx, row in sanc_df.iterrows():
            cid, off_id, score, conf, meth = canonical_lookup.get(("sanctioned", idx), ("", "", np.nan, "NONE", "unmatched"))
            row_wid = str(row.get("work_id", "")).strip()
            if not off_id and row_wid and row_wid != "nan":
                off_id = row_wid
            
            desc = str(row.get("work_description", "")).strip()
            state = str(row.get("state", "")).strip()
            const = str(row.get("constituency", "")).strip()
            mp = str(row.get("mp_name", "")).strip()
            cat = str(row.get("work_category", "")).strip()
            s_amt = pd.to_numeric(row.get("sanction_amount", np.nan), errors="coerce")
            s_date = str(row.get("sanction_date", "")).strip()
            r_date = str(row.get("recommended_date", "")).strip()

            rec = get_or_create_master_record(cid, off_id, state, const, mp, cat, desc)
            rec["has_sanction"] = 1
            rec["sanctioned_amount"] = float(s_amt) if pd.notna(s_amt) else rec["sanctioned_amount"]
            if s_date and s_date != "nan":
                rec["sanction_date"] = s_date
            if r_date and r_date != "nan" and not rec["recommended_date"]:
                rec["recommended_date"] = r_date
            if pd.notna(row.get("work_status")):
                rec["work_status"] = str(row.get("work_status"))
            if pd.notna(row.get("ida_agency")) and not rec["ida_agency"]:
                rec["ida_agency"] = str(row.get("ida_agency"))

    # B. Ingest Recommended
    if not rec_df.empty:
        for idx, row in rec_df.iterrows():
            cid, off_id, score, conf, meth = canonical_lookup.get(("recommended", idx), ("", "", np.nan, "NONE", "unmatched"))
            desc = str(row.get("work_description", "")).strip()
            state = str(row.get("state", "")).strip()
            const = str(row.get("constituency", "")).strip()
            mp = str(row.get("mp_name", "")).strip()
            cat = str(row.get("work_category", "")).strip()
            r_amt = pd.to_numeric(row.get("recommended_amount", np.nan), errors="coerce")
            r_date = str(row.get("recommended_date", "")).strip()
            s_date = str(row.get("sanction_date", "")).strip()

            rec = get_or_create_master_record(cid, off_id, state, const, mp, cat, desc)
            rec["has_recommendation"] = 1
            if pd.notna(r_amt):
                rec["recommended_amount"] = float(r_amt)
            if r_date and r_date != "nan":
                rec["recommended_date"] = r_date
            if s_date and s_date != "nan" and not rec["sanction_date"]:
                rec["sanction_date"] = s_date

    # C. Ingest Completed
    if not comp_df.empty:
        for idx, row in comp_df.iterrows():
            cid, off_id, score, conf, meth = canonical_lookup.get(("completed", idx), ("", "", np.nan, "NONE", "unmatched"))
            desc = str(row.get("work_description", "")).strip()
            state = str(row.get("state", "")).strip()
            const = str(row.get("constituency", "")).strip()
            mp = str(row.get("mp_name", "")).strip()
            cat = str(row.get("work_category", "")).strip()
            c_amt = pd.to_numeric(row.get("expenditure_amount", np.nan), errors="coerce")
            c_date = str(row.get("completion_date", "")).strip()

            rec = get_or_create_master_record(cid, off_id, state, const, mp, cat, desc)
            rec["has_completion"] = 1
            if pd.notna(c_amt):
                rec["completion_amount"] = float(c_amt)
            if c_date and c_date != "nan":
                rec["completion_date"] = c_date

    # D. Aggregate Expenditure into Work Master
    if not transaction_df.empty:
        exp_grouped = transaction_df.groupby("canonical_work_id")
        for cid_val, group in exp_grouped:
            if cid_val in master_records:
                rec = master_records[cid_val]
                rec["has_expenditure"] = 1
                rec["expenditure_amount"] = float(group["transaction_amount"].sum())
                rec["expenditure_transaction_count"] = len(group)
                dates = pd.to_datetime(group["transaction_date"], errors="coerce").dropna().sort_values()
                if not dates.empty:
                    rec["first_expenditure_date"] = dates.iloc[0].strftime("%Y-%m-%d")
                    rec["last_expenditure_date"] = dates.iloc[-1].strftime("%Y-%m-%d")
                vendors = group["vendor_name"].dropna().unique()
                if len(vendors) > 0 and not rec["vendor_name"]:
                    rec["vendor_name"] = str(vendors[0])

    work_master_df = pd.DataFrame(list(master_records.values()))
    
    # Assign canonical IDs if missing
    if not work_master_df.empty:
        for i in range(len(work_master_df)):
            if not work_master_df.at[i, "canonical_work_id"]:
                work_master_df.at[i, "canonical_work_id"] = f"CW_{parliament[:2].upper()}_{i+1:06d}"

    logger.info(f"Built Unified Work Master for [{parliament}]: {len(work_master_df)} unique works")
    return work_master_df, transaction_df

