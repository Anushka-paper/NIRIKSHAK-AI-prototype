import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'nirikshak.db'))
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("UPDATE mp_master SET house = 'Lok Sabha' WHERE mp_id IN (SELECT mp_id FROM mp_alias WHERE source_file LIKE '%(2)%')")
c.execute("UPDATE mp_master SET house = 'Rajya Sabha' WHERE mp_id IN (SELECT mp_id FROM mp_alias WHERE source_file LIKE '%(4)%')")
# Default remaining to Lok Sabha
c.execute("UPDATE mp_master SET house = 'Lok Sabha' WHERE house IS NULL")
conn.commit()

res = c.execute("SELECT house, count(*) FROM mp_master GROUP BY house").fetchall()
print("MP House Distribution:", res)
conn.close()

