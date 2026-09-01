import sqlite3
import os
import glob
import pandas as pd

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Default all current works_recommended to 'Lok Sabha'
c.execute("UPDATE works_recommended SET house = 'Lok Sabha'")
conn.commit()

# Now load Rajya Sabha works_recommended file to get exact work_id_raw for Rajya Sabha
rs_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs', 'RS_DATASET', 'Works Recommended (2).csv'))

if os.path.exists(rs_file):
    print("Reading Rajya Sabha Works Recommended file...")
    df = pd.read_csv(rs_file, low_memory=False)
    raw_works = df['WORK'].dropna().astype(str).tolist()
    
    rs_clean_ids = set()
    for rw in raw_works:
        cleaned = rw.strip().replace("\t", "").replace(" ", "")
        parts = cleaned.split('-')
        if len(parts) > 1 and ("WS/" in parts[0] or "MP" in parts[0]):
            rs_clean_ids.add(parts[0])
        else:
            rs_clean_ids.add(cleaned[:100])
            
    print(f"Extracted {len(rs_clean_ids)} unique Rajya Sabha work IDs.")
    
    # Tag matching works_recommended as 'Rajya Sabha'
    c.executemany(
        "UPDATE works_recommended SET house = 'Rajya Sabha' WHERE work_id_raw = ?",
        [(wid,) for wid in rs_clean_ids]
    )
    conn.commit()
    
    # Also update mp_master house for Rajya Sabha MPs
    mp_names = df["Hon'ble Members of Parliament"].dropna().unique()
    for mp in mp_names:
        clean_name = mp.strip().replace("Shri ", "").replace("Smt. ", "").replace("Dr. ", "")
        import re
        clean_name = re.sub(r'\s*\(\d{4}-\d{2,4}\).*$', '', clean_name).strip()
        c.execute("UPDATE mp_master SET house = 'Rajya Sabha' WHERE canonical_name = ?", (clean_name,))
    conn.commit()

res = c.execute("SELECT house, count(*) FROM works_recommended GROUP BY house").fetchall()
print("Works House Distribution:", res)

res_mp = c.execute("SELECT house, count(*) FROM mp_master GROUP BY house").fetchall()
print("MP House Distribution:", res_mp)

conn.close()

