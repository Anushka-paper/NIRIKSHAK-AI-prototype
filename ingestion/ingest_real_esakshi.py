import os
import sys
import glob
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.models import (
    Base, MPMaster, MPAlias, Geography, IDAMaster, VendorMaster, VendorAlias,
    WorkRecommended, WorkSanctioned, Expenditure, WorkCompleted, CalamityConsent, Allocation
)
from ingestion.cleaning.currency import clean_currency_to_paise
from ingestion.cleaning.dates import standardize_date
from ingestion.entity_resolution.work_id_parser import parse_work_id

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

def get_db():
    return Session()

def find_file(directory, pattern):
    matches = glob.glob(os.path.join(directory, pattern))
    if matches:
        return matches[0]
    return None

def clean_mp_name(raw_name):
    if not isinstance(raw_name, str) or not raw_name.strip():
        return "Unknown MP"
    name = raw_name.strip()
    name = re.sub(r'^Shri\s+|^Smt\.\s+|^Dr\.\s+|^Prof\.\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(\d{4}-\d{2,4}\).*$', '', name)
    return name.strip()

def clean_work_id(raw_work):
    if not isinstance(raw_work, str):
        return str(raw_work)
    parsed = parse_work_id(raw_work)
    if parsed:
        return parsed
    cleaned = raw_work.strip().replace("\t", "").replace(" ", "")
    parts = cleaned.split('-')
    if len(parts) > 1 and ("WS/" in parts[0] or "MP" in parts[0]):
        return parts[0]
    return cleaned[:100]

def ingest_dataset(house_name, folder_path):
    print(f"\n==========================================")
    print(f"Ingesting {house_name} Dataset from {folder_path}...")
    print(f"==========================================")
    
    db = get_db()
    
    # 1. MP Master & Allocations
    alloc_file = find_file(folder_path, "Allocated Limit*.csv")
    if alloc_file:
        print(f"Loading MPs & Allocations from {os.path.basename(alloc_file)}...")
        df_alloc = pd.read_csv(alloc_file)
        for _, row in df_alloc.iterrows():
            raw_mp = row.get("Hon'ble Members of Parliaments") or row.get("Hon'ble Members of Parliament")
            mp_name = clean_mp_name(raw_mp)
            state_name = str(row.get("State", "Unknown")).strip()
            
            geo = db.query(Geography).filter(Geography.name == state_name).first()
            if not geo:
                geo = Geography(level="state", name=state_name)
                db.add(geo)
                db.flush()
                
            mp = db.query(MPMaster).filter(MPMaster.canonical_name == mp_name).first()
            if not mp:
                mp = MPMaster(canonical_name=mp_name, house=house_name, state_id=geo.geo_id)
                db.add(mp)
                db.flush()
                alias = MPAlias(mp_id=mp.mp_id, raw_name=str(raw_mp), source_file=os.path.basename(alloc_file))
                db.add(alias)
            else:
                if not mp.house:
                    mp.house = house_name
            
            alloc_amt = clean_currency_to_paise(row.get("Allocated AMOUNT ( ₹ )", 0))
            if alloc_amt > 0:
                existing_alloc = db.query(Allocation).filter(
                    Allocation.mp_id == mp.mp_id,
                    Allocation.fiscal_year == "2024-2025"
                ).first()
                if not existing_alloc:
                    alloc = Allocation(mp_id=mp.mp_id, fiscal_year="2024-2025", allocated_amount=alloc_amt)
                    db.add(alloc)
        db.commit()

    # Get default MP and IDA for placeholders
    default_mp = db.query(MPMaster).first()
    default_mp_id = default_mp.mp_id if default_mp else 1
    
    default_ida = db.query(IDAMaster).first()
    if not default_ida:
        default_ida = IDAMaster(name="General IDA", state_id=1)
        db.add(default_ida)
        db.flush()
    default_ida_id = default_ida.ida_id

    # 2. Works Recommended
    rec_file = find_file(folder_path, "Works Recommended*.csv")
    if rec_file:
        print(f"Loading Recommended Works from {os.path.basename(rec_file)}...")
        df_rec = pd.read_csv(rec_file, low_memory=False)
        rec_count = 0
        for _, row in df_rec.iterrows():
            raw_work = row.get("WORK") or row.get("Work")
            if not raw_work or pd.isna(raw_work):
                continue
            
            work_id_raw = clean_work_id(raw_work)
            raw_mp = row.get("Hon'ble Members of Parliament")
            mp_name = clean_mp_name(raw_mp)
            
            mp = db.query(MPMaster).filter(MPMaster.canonical_name == mp_name).first()
            mp_id = mp.mp_id if mp else default_mp_id
            
            ida_raw = str(row.get("IDA", "Unknown")).strip()
            ida = db.query(IDAMaster).filter(IDAMaster.name == ida_raw).first()
            if not ida:
                ida = IDAMaster(name=ida_raw, state_id=1)
                db.add(ida)
                db.flush()
            
            rec_amt = clean_currency_to_paise(row.get("RECOMMENDED AMOUNT   ( ₹ )", 0))
            rec_date = standardize_date(row.get("Recommended date"))
            category = str(row.get("Work category", "Other")).strip()
            description = str(row.get("Work description", "")).strip()
            
            existing = db.query(WorkRecommended).filter(WorkRecommended.work_id_raw == work_id_raw).first()
            if not existing:
                wr = WorkRecommended(
                    work_id_raw=work_id_raw,
                    house=house_name,
                    mp_id=mp_id,
                    ida_id=ida.ida_id,
                    category=category,
                    description=description,
                    recommended_amount=rec_amt,
                    recommendation_date=rec_date
                )
                db.add(wr)
                rec_count += 1
                if rec_count % 5000 == 0:
                    db.commit()
                    print(f"  Processed {rec_count} recommended works...")
            else:
                if not existing.house:
                    existing.house = house_name
        db.commit()
        print(f"  Finished: {rec_count} new recommended works ingested.")

    # 3. Works Sanctioned
    sanc_file = find_file(folder_path, "Works Sanctioned*.csv")
    if sanc_file:
        print(f"Loading Sanctioned Works from {os.path.basename(sanc_file)}...")
        df_sanc = pd.read_csv(sanc_file, low_memory=False)
        sanc_count = 0
        for _, row in df_sanc.iterrows():
            raw_work = row.get("Work") or row.get("WORK")
            if not raw_work or pd.isna(raw_work):
                continue
            work_id_raw = clean_work_id(raw_work)
            
            wr = db.query(WorkRecommended).filter(WorkRecommended.work_id_raw == work_id_raw).first()
            if not wr:
                sanc_amt = clean_currency_to_paise(row.get("Sanction Amount ( ₹ )", 0))
                wr = WorkRecommended(
                    work_id_raw=work_id_raw,
                    house=house_name,
                    mp_id=default_mp_id,
                    ida_id=default_ida_id,
                    category=str(row.get("Work category", "Other")).strip(),
                    description=str(row.get("Work description", work_id_raw)).strip(),
                    recommended_amount=sanc_amt,
                    recommendation_date=standardize_date(row.get("Recommended date"))
                )
                db.add(wr)
                db.flush()
            else:
                if not wr.house:
                    wr.house = house_name

            existing_sanc = db.query(WorkSanctioned).filter(WorkSanctioned.work_id == wr.work_id).first()
            if not existing_sanc:
                sanc_amt = clean_currency_to_paise(row.get("Sanction Amount ( ₹ )", 0))
                sanc_date = standardize_date(row.get("Sanction Date"))
                ws = WorkSanctioned(
                    work_id=wr.work_id,
                    sanctioned_amount=sanc_amt,
                    sanction_date=sanc_date
                )
                db.add(ws)
                sanc_count += 1
                if sanc_count % 5000 == 0:
                    db.commit()
                    print(f"  Processed {sanc_count} sanctioned works...")
        db.commit()
        print(f"  Finished: {sanc_count} sanctioned works ingested.")

    # 4. Expenditure
    exp_file = find_file(folder_path, "Expenditure on Completed*.csv")
    if exp_file:
        print(f"Loading Expenditure Data from {os.path.basename(exp_file)}...")
        df_exp = pd.read_csv(exp_file, low_memory=False)
        exp_count = 0
        for _, row in df_exp.iterrows():
            raw_work = row.get("Work ID") or row.get("Work")
            if not raw_work or pd.isna(raw_work):
                continue
            work_id_raw = clean_work_id(raw_work)
            
            wr = db.query(WorkRecommended).filter(WorkRecommended.work_id_raw == work_id_raw).first()
            if not wr:
                amt = clean_currency_to_paise(row.get("Fund Disbursed Amount ( ₹ )", 0))
                wr = WorkRecommended(
                    work_id_raw=work_id_raw,
                    house=house_name,
                    mp_id=default_mp_id,
                    ida_id=default_ida_id,
                    category="Other",
                    description=str(row.get("Work", work_id_raw)).strip(),
                    recommended_amount=amt
                )
                db.add(wr)
                db.flush()
            else:
                if not wr.house:
                    wr.house = house_name
                
            vendor_name = str(row.get("Vendor Name", "Unknown Vendor")).strip()
            vendor = db.query(VendorMaster).filter(VendorMaster.canonical_name == vendor_name).first()
            if not vendor:
                vendor = VendorMaster(canonical_name=vendor_name)
                db.add(vendor)
                db.flush()
            
            amt = clean_currency_to_paise(row.get("Fund Disbursed Amount ( ₹ )", 0))
            txn_date = standardize_date(row.get("Expenditure Date"))
            status = str(row.get("Payment Status", "Disbursed")).strip()
            
            exp = Expenditure(
                work_id=wr.work_id,
                vendor_id=vendor.vendor_id,
                amount=amt,
                txn_date=txn_date,
                payment_status=status
            )
            db.add(exp)
            exp_count += 1
            if exp_count % 5000 == 0:
                db.commit()
                print(f"  Processed {exp_count} transactions...")
        db.commit()
        print(f"  Finished: {exp_count} expenditure transactions ingested.")

    # 5. Works Completed
    comp_file = find_file(folder_path, "Works Completed*.csv")
    if comp_file:
        print(f"Loading Completed Works from {os.path.basename(comp_file)}...")
        df_comp = pd.read_csv(comp_file, low_memory=False)
        comp_count = 0
        for _, row in df_comp.iterrows():
            raw_work = row.get("Work") or row.get("WORK")
            if not raw_work or pd.isna(raw_work):
                continue
            work_id_raw = clean_work_id(raw_work)
            
            wr = db.query(WorkRecommended).filter(WorkRecommended.work_id_raw == work_id_raw).first()
            if wr:
                existing_comp = db.query(WorkCompleted).filter(WorkCompleted.work_id == wr.work_id).first()
                if not existing_comp:
                    comp_date = standardize_date(row.get("Completion Date"))
                    has_img = str(row.get("Image", "")).lower() not in ["n/a", "", "nan", "none"]
                    wc = WorkCompleted(
                        work_id=wr.work_id,
                        completion_date=comp_date,
                        status="Completed",
                        has_completion_evidence=has_img
                    )
                    db.add(wc)
                    comp_count += 1
        db.commit()
        print(f"  Finished: {comp_count} completed works ingested.")

    # 6. Calamity Consents
    cal_file = find_file(folder_path, "Amount consented for Calamity*.csv")
    if cal_file:
        print(f"Loading Calamity Consents from {os.path.basename(cal_file)}...")
        df_cal = pd.read_csv(cal_file, low_memory=False)
        for _, row in df_cal.iterrows():
            raw_mp = row.get("Hon'ble Members of Parliament")
            mp_name = clean_mp_name(raw_mp)
            mp = db.query(MPMaster).filter(MPMaster.canonical_name == mp_name).first()
            mp_id = mp.mp_id if mp else default_mp_id
            
            cal_amt = clean_currency_to_paise(row.get("Consent Amount ( ₹ )", 0))
            cal_date = standardize_date(row.get("Date of Consent"))
            cal_type = str(row.get("Calamity Type", "Calamity")).strip()
            
            cc = CalamityConsent(
                mp_id=mp_id,
                calamity_type=cal_type,
                amount=cal_amt,
                consent_date=cal_date
            )
            db.add(cc)
        db.commit()
        print("  Finished: Calamity consents ingested.")
        
    db.close()
    print(f"Finished ingesting {house_name}!")

if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs'))
    
    ls_dir = os.path.join(BASE_DIR, 'LS_DATASET')
    rs_dir = os.path.join(BASE_DIR, 'RS_DATASET')
    
    if os.path.exists(ls_dir):
        ingest_dataset("Lok Sabha", ls_dir)
    else:
        print(f"Directory not found: {ls_dir}")
        
    if os.path.exists(rs_dir):
        ingest_dataset("Rajya Sabha", rs_dir)
    else:
        print(f"Directory not found: {rs_dir}")

