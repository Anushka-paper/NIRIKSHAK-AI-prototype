import sqlite3
import os
import re
import pandas as pd

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

ls_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'LS_DATASET', 'Works Recommended (4).csv'))
rs_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Works Recommended (2).csv'))

def parse_work_ids_from_csv(csv_path):
    print(f"Reading {os.path.basename(csv_path)}...")
    df = pd.read_csv(csv_path, low_memory=False)
    raw_works = df['WORK'].dropna().astype(str).tolist()
    clean_ids = set()
    for rw in raw_works:
        cleaned = rw.strip().replace("\t", "").replace(" ", "")
        parts = cleaned.split('-')
        if len(parts) > 1 and ("WS/" in parts[0] or "MP" in parts[0]):
            clean_ids.add(parts[0])
        else:
            clean_ids.add(cleaned[:100])
    return clean_ids, df

print("1. Tagging Lok Sabha Works...")
ls_ids, ls_df = parse_work_ids_from_csv(ls_file)
c.executemany(
    "UPDATE works_recommended SET house = 'Lok Sabha' WHERE work_id_raw = ?",
    [(wid,) for wid in ls_ids]
)
conn.commit()

print("2. Tagging Rajya Sabha Works...")
rs_ids, rs_df = parse_work_ids_from_csv(rs_file)
c.executemany(
    "UPDATE works_recommended SET house = 'Rajya Sabha' WHERE work_id_raw = ?",
    [(wid,) for wid in rs_ids]
)
conn.commit()

# Tag Rajya Sabha MPs
rs_alloc_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Allocated Limit for Honble MPs (4).csv'))
if os.path.exists(rs_alloc_file):
    df_alloc = pd.read_csv(rs_alloc_file)
    for raw_mp in df_alloc["Hon'ble Members of Parliament"].dropna():
        name = str(raw_mp).strip()
        name = re.sub(r'^Shri\s+|^Smt\.\s+|^Dr\.\s+|^Prof\.\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\(\d{4}-\d{2,4}\).*$', '', name).strip()
        c.execute("UPDATE mp_master SET house = 'Rajya Sabha' WHERE canonical_name LIKE ?", (f"%{name}%",))
conn.commit()

# Print results
print("\n--- FINAL HOUSE DISTRIBUTION IN DB ---")
res_works = c.execute("SELECT house, count(*) FROM works_recommended GROUP BY house").fetchall()
print("Works Recommended by House:", res_works)

res_mps = c.execute("SELECT house, count(*) FROM mp_master GROUP BY house").fetchall()
print("MPs Master by House:", res_mps)

conn.close()

