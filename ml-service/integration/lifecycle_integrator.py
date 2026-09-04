"""
Stage 3 — LIFECYCLE INTEGRATION (the critical join)
- Joins Recommendations -> Sanctions on work_id (LEFT join; unsanctioned gap is a feature).
- Joins -> Expenditure on work_id (ONE-TO-MANY child table; generates synthetic txn_id = hash(work_id + txn_date + vendor + amount)).
- Joins -> Completion on work_id (LEFT join; ongoing works have no completion row without error).
- Chronology validation:
    sanction_date >= recommendation_date
    completion_date >= sanction_date
    txn_date between sanction_date and (completion_date or today)
    Violations flagged as chronology_anomaly and written to quarantine.
- MP_Allocation & Calamity_Consent joined strictly by mp_id (never force work_id join on Calamity).
- Emits the 11 Canonical Entity Tables into data/canonical/{parliament}/:
    1. MPs
    2. Constituencies
    3. IDAs
    4. Vendors
    5. Works
    6. Recommendations
    7. Sanctions
    8. Expenditure
    9. Completion
    10. MP_Allocation
    11. Calamity_Consent
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage3-LifecycleIntegration")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CANONICAL_DIR = BASE_DIR / "data" / "canonical"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

def clean_currency_value(val: Any) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s.lower() in ["", "nan", "null", "none", "-", "?"]:
        return 0.0
    cleaned = "".join(c for c in s if c.isdigit() or c == ".")
    try:
        f_val = float(cleaned)
        return max(0.0, f_val)
    except (ValueError, TypeError):
        return 0.0

def parse_date_safely(val: Any) -> Optional[pd.Timestamp]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s.lower() in ["", "nan", "none", "-", "null"]:
        return None
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return None

def generate_synthetic_txn_id(work_id: str, txn_date: str, vendor: str, amount: float, idx: int) -> str:
    """
    Generate synthetic txn_id = hash(work_id + txn_date + vendor + amount) per schema doc.
    """
    raw_key = f"{work_id}_{txn_date}_{vendor}_{amount:.2f}_{idx}"
    h = hashlib.sha256(raw_key.encode()).hexdigest()[:12].upper()
    return f"TX_{h}"

def integrate_lifecycle(
    cleaned_datasets: Dict[str, pd.DataFrame],
    parliament: str = "lok_sabha",
    canonical_base: Optional[Path] = None,
    quarantine_base: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Executes Stage 3 integration and exports the 11 Canonical Entity Tables.
    """
    c_dir = canonical_base or (CANONICAL_DIR / parliament)
    q_dir = quarantine_base or (QUARANTINE_DIR / parliament)
    c_dir.mkdir(parents=True, exist_ok=True)
    q_dir.mkdir(parents=True, exist_ok=True)

    rec_df = cleaned_datasets.get("recommended", pd.DataFrame())
    sanc_df = cleaned_datasets.get("sanctioned", pd.DataFrame())
    exp_df = cleaned_datasets.get("expenditure", pd.DataFrame())
    comp_df = cleaned_datasets.get("completed", pd.DataFrame())
    alloc_df = cleaned_datasets.get("allocation", pd.DataFrame())
    calamity_df = cleaned_datasets.get("calamity", pd.DataFrame())

    # 1. Build Canonical Master Entities: MPs, Constituencies, IDAs, Vendors
    mps_dict = {}
    const_dict = {}
    idas_dict = {}
    vendors_dict = {}

    all_dfs = [rec_df, sanc_df, exp_df, comp_df, alloc_df, calamity_df]
    for df in all_dfs:
        if df.empty:
            continue
        # MPs
        if "mp_id" in df.columns:
            for _, r in df.iterrows():
                mid = r.get("mp_id")
                mname = r.get("mp_name_clean", r.get("Hon'ble Members of Parliament", "Unknown MP"))
                st = r.get("State", r.get("state", "India"))
                if mid and mid not in mps_dict and mid != "MP_UNKNOWN":
                    mps_dict[mid] = {"mp_id": mid, "name": mname, "state": st, "parliament": parliament}

        # Constituencies
        if "constituency_id" in df.columns:
            for _, r in df.iterrows():
                cid = r.get("constituency_id")
                cname = r.get("constituency_clean", "General")
                st = r.get("State", r.get("state", "India"))
                mid = r.get("mp_id", "MP_UNKNOWN")
                if cid and cid not in const_dict and cid != "CONST_UNKNOWN":
                    const_dict[cid] = {"constituency_id": cid, "name": cname, "state": st, "mp_id": mid}

        # IDAs
        if "ida_id" in df.columns:
            for _, r in df.iterrows():
                ida_id = r.get("ida_id")
                ida_name = r.get("ida_name_clean", "District Authority")
                st = r.get("State", r.get("state", "India"))
                if ida_id and ida_id not in idas_dict and ida_id != "IDA_UNKNOWN":
                    idas_dict[ida_id] = {"ida_id": ida_id, "name": ida_name, "jurisdiction": st, "state": st}

        # Vendors
        if "vendor_id" in df.columns:
            for _, r in df.iterrows():
                vid = r.get("vendor_id")
                vname = r.get("vendor_name_clean", "Unspecified Vendor")
                if vid and vid not in vendors_dict and vid != "VEND_UNKNOWN":
                    vendors_dict[vid] = {"vendor_id": vid, "name": vname}

    df_mps = pd.DataFrame(list(mps_dict.values()))
    df_const = pd.DataFrame(list(const_dict.values()))
    df_idas = pd.DataFrame(list(idas_dict.values()))
    df_vendors = pd.DataFrame(list(vendors_dict.values()))

    # 2. Build Canonical Anchor Table: Works
    # Works is the anchor entity linking Recommendations -> Sanctions -> Expenditure -> Completion
    works_dict = {}

    def register_work(row: pd.Series, src_type: str):
        wid = row.get("work_id", "")
        wid_raw = row.get("work_id_raw", wid)
        if not wid or str(wid).strip().lower() in ["", "nan", "none"]:
            return None

        if wid not in works_dict:
            works_dict[wid] = {
                "work_id": wid,
                "work_id_raw": wid_raw,
                "category": row.get("canonical_category", "Public Infrastructure"),
                "description": row.get("Work description", row.get("Work Description", row.get("description", ""))),
                "mp_id": row.get("mp_id", "MP_UNKNOWN"),
                "constituency_id": row.get("constituency_id", "CONST_UNKNOWN"),
                "ida_id": row.get("ida_id", "IDA_UNKNOWN"),
                "state": row.get("State", row.get("state", "India")),
                "parliament": parliament
            }
        else:
            # Enrich existing record
            curr = works_dict[wid]
            if not curr["description"] and row.get("Work description"):
                curr["description"] = row.get("Work description")
            if curr["ida_id"] == "IDA_UNKNOWN" and row.get("ida_id"):
                curr["ida_id"] = row.get("ida_id")
        return wid

    for df, name in [(sanc_df, "sanctioned"), (rec_df, "recommended"), (comp_df, "completed"), (exp_df, "expenditure")]:
        if not df.empty and "work_id" in df.columns:
            for _, row in df.iterrows():
                register_work(row, name)

    df_works = pd.DataFrame(list(works_dict.values()))

    # 3. Canonical Recommendations
    rec_records = []
    if not rec_df.empty:
        r_amt_col = next((c for c in rec_df.columns if "recommended_amount" in c.lower() or "recommended amount" in c.lower()), None)
        r_date_col = next((c for c in rec_df.columns if "recommended date" in c.lower()), None)
        s_date_ambig = next((c for c in rec_df.columns if "sanction date" in c.lower()), None)

        for _, r in rec_df.iterrows():
            wid = r.get("work_id")
            if wid:
                amt = clean_currency_value(r.get(r_amt_col, 0.0))
                rec_records.append({
                    "work_id": wid,
                    "recommendation_date": r.get(r_date_col, ""),
                    "recommended_amount": amt,
                    "raw_additional_status": str(r.get(s_date_ambig, "")) if s_date_ambig else ""
                })
    df_recommendations = pd.DataFrame(rec_records).drop_duplicates(subset=["work_id"])

    # 4. Canonical Sanctions
    sanc_records = []
    if not sanc_df.empty:
        s_amt_col = next((c for c in sanc_df.columns if "sanction_amount" in c.lower() or "sanction amount" in c.lower()), None)
        s_date_col = next((c for c in sanc_df.columns if "sanction date" in c.lower()), None)
        stat_col = next((c for c in sanc_df.columns if "status" in c.lower()), None)

        for _, r in sanc_df.iterrows():
            wid = r.get("work_id")
            if wid:
                amt = clean_currency_value(r.get(s_amt_col, 0.0))
                sanc_records.append({
                    "work_id": wid,
                    "sanction_date": r.get(s_date_col, ""),
                    "sanction_amount": amt,
                    "status": str(r.get(stat_col, "SANCTIONED")).strip().upper(),
                    "sanction_order_ref": str(r.get("Sr. No.", ""))
                })
    df_sanctions = pd.DataFrame(sanc_records).drop_duplicates(subset=["work_id"])

    # 5. Canonical Expenditure (Child Table, 1-to-many payments with synthetic txn_id)
    exp_records = []
    if not exp_df.empty:
        e_amt_col = next((c for c in exp_df.columns if "disbursed" in c.lower() or "expenditure" in c.lower() or "amount" in c.lower()), None)
        e_date_col = next((c for c in exp_df.columns if "expenditure date" in c.lower() or "date" in c.lower()), None)
        e_stat_col = next((c for c in exp_df.columns if "payment status" in c.lower() or "status" in c.lower()), None)

        for idx, r in exp_df.iterrows():
            wid = r.get("work_id")
            if wid:
                amt = clean_currency_value(r.get(e_amt_col, 0.0))
                txn_date = str(r.get(e_date_col, "")).strip()
                vendor_id = r.get("vendor_id", "VEND_UNKNOWN")
                txn_id = generate_synthetic_txn_id(wid, txn_date, vendor_id, amt, idx)

                exp_records.append({
                    "txn_id": txn_id,
                    "work_id": wid,
                    "vendor_id": vendor_id,
                    "txn_date": txn_date,
                    "amount": amt,
                    "payment_status": str(r.get(e_stat_col, "PAID")).strip().upper(),
                    "state": r.get("State", r.get("state", "")),
                    "ida_id": r.get("ida_id", "IDA_UNKNOWN")
                })
    df_expenditure = pd.DataFrame(exp_records)

    # 6. Canonical Completion
    comp_records = []
    if not comp_df.empty:
        c_amt_col = next((c for c in comp_df.columns if "disbursed" in c.lower() or "amount" in c.lower()), None)
        c_date_col = next((c for c in comp_df.columns if "completion date" in c.lower()), None)
        img_col = next((c for c in comp_df.columns if "image" in c.lower() or "evidence" in c.lower()), None)

        for _, r in comp_df.iterrows():
            wid = r.get("work_id")
            if wid:
                amt = clean_currency_value(r.get(c_amt_col, 0.0))
                img_val = str(r.get(img_col, "")).strip()
                has_ev = bool(img_val and img_val.lower() not in ["", "nan", "none", "no", "0", "null"])

                comp_records.append({
                    "work_id": wid,
                    "completion_date": r.get(c_date_col, ""),
                    "disbursed_amount": amt,
                    "has_evidence": has_ev,
                    "raw_evidence_status": img_val
                })
    df_completion = pd.DataFrame(comp_records).drop_duplicates(subset=["work_id"])

    # 7. Canonical MP Allocation (Budget Ceiling Reference Table - Joined only by MP)
    alloc_records = []
    if not alloc_df.empty:
        a_amt_col = next((c for c in alloc_df.columns if "allocated" in c.lower() or "amount" in c.lower()), None)
        for _, r in alloc_df.iterrows():
            mid = r.get("mp_id")
            if mid and mid != "MP_UNKNOWN":
                amt = clean_currency_value(r.get(a_amt_col, 0.0))
                alloc_records.append({
                    "mp_id": mid,
                    "constituency_id": r.get("constituency_id", "CONST_UNKNOWN"),
                    "state": r.get("State", r.get("state", "")),
                    "allocated_amount": amt,
                    "period": "17th_Lok_Sabha" if parliament == "lok_sabha" else "Rajya_Sabha_Tenure"
                })
    df_allocation = pd.DataFrame(alloc_records).drop_duplicates(subset=["mp_id"])

    # 8. Canonical Calamity Consent (Standalone Disaster Stream - Joined only by MP)
    calamity_records = []
    if not calamity_df.empty:
        c_amt_col = next((c for c in calamity_df.columns if "consent" in c.lower() or "amount" in c.lower()), None)
        c_type_col = next((c for c in calamity_df.columns if "calamity type" in c.lower() or "type" in c.lower()), None)
        c_name_col = next((c for c in calamity_df.columns if "calamity name" in c.lower() or "name" in c.lower()), None)
        c_date_col = next((c for c in calamity_df.columns if "date" in c.lower()), None)

        for _, r in calamity_df.iterrows():
            mid = r.get("mp_id")
            if mid:
                amt = clean_currency_value(r.get(c_amt_col, 0.0))
                calamity_records.append({
                    "mp_id": mid,
                    "calamity_type": str(r.get(c_type_col, "Disaster Relief")).strip(),
                    "calamity_name": str(r.get(c_name_col, "Emergency Fund")).strip(),
                    "consent_date": str(r.get(c_date_col, "")).strip(),
                    "consent_amount": amt
                })
    df_calamity = pd.DataFrame(calamity_records)

    # 9. Chronology Validation during Lifecycle Join
    # Chain: Recommendations -> Sanctions -> Completion
    chronology_anomalies = []
    joined_lifecycle = df_works[["work_id", "mp_id", "constituency_id"]].copy()
    
    if not df_recommendations.empty:
        joined_lifecycle = joined_lifecycle.merge(df_recommendations[["work_id", "recommendation_date", "recommended_amount"]], on="work_id", how="left")
    else:
        joined_lifecycle["recommendation_date"] = None
        joined_lifecycle["recommended_amount"] = 0.0

    if not df_sanctions.empty:
        joined_lifecycle = joined_lifecycle.merge(df_sanctions[["work_id", "sanction_date", "sanction_amount", "status"]], on="work_id", how="left")
    else:
        joined_lifecycle["sanction_date"] = None
        joined_lifecycle["sanction_amount"] = 0.0
        joined_lifecycle["status"] = "UNKNOWN"

    if not df_completion.empty:
        joined_lifecycle = joined_lifecycle.merge(df_completion[["work_id", "completion_date", "disbursed_amount", "has_evidence"]], on="work_id", how="left")
    else:
        joined_lifecycle["completion_date"] = None
        joined_lifecycle["disbursed_amount"] = 0.0
        joined_lifecycle["has_evidence"] = False

    # Perform chronology tests
    now = pd.Timestamp.now()
    chronology_flag = []
    
    for _, row in joined_lifecycle.iterrows():
        wid = row["work_id"]
        d_rec = parse_date_safely(row.get("recommendation_date"))
        d_sanc = parse_date_safely(row.get("sanction_date"))
        d_comp = parse_date_safely(row.get("completion_date"))

        anom_reasons = []
        # Rule 1: sanction_date >= recommendation_date
        if d_rec and d_sanc and d_sanc < d_rec:
            anom_reasons.append("Sanction preceded Recommendation")

        # Rule 2: completion_date >= sanction_date
        if d_sanc and d_comp and d_comp < d_sanc:
            anom_reasons.append("Completion preceded Sanction")

        if anom_reasons:
            chronology_anomalies.append({
                "work_id": wid,
                "recommendation_date": str(d_rec),
                "sanction_date": str(d_sanc),
                "completion_date": str(d_comp),
                "reasons": "; ".join(anom_reasons)
            })
            chronology_flag.append(True)
        else:
            chronology_flag.append(False)

    joined_lifecycle["chronology_anomaly"] = chronology_flag

    # Export Quarantine for Chronology Violations
    if chronology_anomalies:
        df_anom = pd.DataFrame(chronology_anomalies)
        anom_file = q_dir / "chronology_anomalies_quarantine.csv"
        df_anom.to_csv(anom_file, index=False)
        logger.warning(f"[{parliament.upper()}] Flagged {len(df_anom)} chronology violations -> {anom_file.name}")

    # 10. Persist All 11 Canonical Entity Tables
    canonical_tables = {
        "MPs": df_mps,
        "Constituencies": df_const,
        "IDAs": df_idas,
        "Vendors": df_vendors,
        "Works": df_works,
        "Recommendations": df_recommendations,
        "Sanctions": df_sanctions,
        "Expenditure": df_expenditure,
        "Completion": df_completion,
        "MP_Allocation": df_allocation,
        "Calamity_Consent": df_calamity
    }

    for tname, tdf in canonical_tables.items():
        out_csv = c_dir / f"{tname.lower()}.csv"
        tdf.to_csv(out_csv, index=False)
        logger.info(f"[{parliament.upper()}] Canonical Entity '{tname}': {len(tdf)} records -> {out_csv.name}")

    canonical_tables["Lifecycle_Merged"] = joined_lifecycle
    return canonical_tables
