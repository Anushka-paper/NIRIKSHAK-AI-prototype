import sqlite3
import os
import pandas as pd
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingestion.cleaning.currency import clean_currency_to_paise
from ingestion.cleaning.dates import standardize_date
from ingestion.entity_resolution.work_id_parser import parse_work_id

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

rs_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Works Recommended (2).csv'))

print(f"Reading {rs_file}...")
df = pd.read_csv(rs_file, low_memory=False)
print(f"Total Rajya Sabha rows to insert: {len(df)}")

inserted = 0
for idx, row in df.iterrows():
    raw_work = row.get("WORK")
    if not raw_work or pd.isna(raw_work):
        continue
        
    cleaned = str(raw_work).strip().replace("\t", "").replace(" ", "")
    parts = cleaned.split('-')
    if len(parts) > 1 and ("WS/" in parts[0] or "MP" in parts[0]):
        work_id_raw = parts[0]
    else:
        work_id_raw = cleaned[:100]
        
    category = str(row.get("Work category", "Other")).strip()
    description = str(row.get("Work description", "")).strip()
    rec_amt = clean_currency_to_paise(row.get("RECOMMENDED AMOUNT   ( ₹ )", 0))
    rec_date_dt = standardize_date(row.get("Recommended date"))
    rec_date_str = rec_date_dt.isoformat() if rec_date_dt else None
    
    # Insert work_recommended with house='Rajya Sabha', mp_id=1, ida_id=1
    c.execute("""
        INSERT INTO works_recommended 
        (work_id_raw, house, mp_id, ida_id, category, description, recommended_amount, recommendation_date)
        VALUES (?, 'Rajya Sabha', 1, 1, ?, ?, ?, ?)
    """, (work_id_raw, category, description, rec_amt, rec_date_str))
    
    inserted += 1
    if inserted % 5000 == 0:
        conn.commit()
        print(f"  Inserted {inserted} Rajya Sabha works...")

conn.commit()
print(f"\nSuccessfully inserted {inserted} Rajya Sabha works into works_recommended!")

# Check updated distribution
res = c.execute("SELECT house, count(*), sum(recommended_amount)/1000000000.0 FROM works_recommended GROUP BY house").fetchall()
print("\n--- FINAL WORKS DISTRIBUTION BY HOUSE ---")
for house, count, amt_cr in res:
    print(f"  • {house}: {count:,} works | ₹{amt_cr:.2f} Cr Budget")

conn.close()

