import sqlite3
import os
import re
import pandas as pd

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

rs_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Works Recommended (2).csv'))

if os.path.exists(rs_file):
    print("1. Reading RS Works Recommended CSV...")
    df = pd.read_csv(rs_file, low_memory=False)
    
    # RS Work ID prefix pattern: WS/MP187 or WS/MP...
    # In RS dataset, work_id_raw contains WS/MP...
    # Let's get list of raw work strings from RS CSV
    rs_works = df['WORK'].dropna().astype(str).tolist()
    
    clean_rs_ids = []
    for rw in rs_works:
        cleaned = rw.strip().replace("\t", "").replace(" ", "")
        parts = cleaned.split('-')
        if len(parts) > 1 and ("WS/" in parts[0] or "MP" in parts[0]):
            clean_rs_ids.append(parts[0])
        else:
            clean_rs_ids.append(cleaned[:100])
            
    print(f"Total RS Work records in CSV: {len(clean_rs_ids)}")
    
    # Tag all these work_id_raw records in works_recommended as 'Rajya Sabha'
    print("2. Tagging matching works_recommended in DB as 'Rajya Sabha'...")
    
    # Batch update SQLite in chunks
    chunk_size = 900
    for i in range(0, len(clean_rs_ids), chunk_size):
        chunk = clean_rs_ids[i:i+chunk_size]
        placeholders = ','.join(['?'] * len(chunk))
        c.execute(f"UPDATE works_recommended SET house = 'Rajya Sabha' WHERE work_id_raw IN ({placeholders})", chunk)
    conn.commit()

# Also tag Rajya Sabha MPs
rs_alloc_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Allocated Limit for Honble MPs (4).csv'))
if os.path.exists(rs_alloc_file):
    print("3. Tagging Rajya Sabha MPs...")
    df_alloc = pd.read_csv(rs_alloc_file)
    for raw_mp in df_alloc["Hon'ble Members of Parliament"].dropna():
        name = str(raw_mp).strip()
        name = re.sub(r'^Shri\s+|^Smt\.\s+|^Dr\.\s+|^Prof\.\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\(\d{4}-\d{2,4}\).*$', '', name).strip()
        c.execute("UPDATE mp_master SET house = 'Rajya Sabha' WHERE canonical_name LIKE ?", (f"%{name}%",))
    conn.commit()

print("\n--- UPDATED HOUSE DISTRIBUTION ---")
res_works = c.execute("SELECT house, count(*) FROM works_recommended GROUP BY house").fetchall()
print("Works Recommended by House:", res_works)

res_mps = c.execute("SELECT house, count(*) FROM mp_master GROUP BY house").fetchall()
print("MPs Master by House:", res_mps)

conn.close()

