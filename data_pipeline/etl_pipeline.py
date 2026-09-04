import os
import pandas as pd
import duckdb

LS_DIR = os.path.join(os.path.dirname(__file__), "LS_DATASET")
RS_DIR = os.path.join(os.path.dirname(__file__), "RS_DATASET")
DB_PATH = os.path.join(os.path.dirname(__file__), "parliament_data.duckdb")

def run_etl():
    print(f"Connecting to DuckDB at {DB_PATH}")
    conn = duckdb.connect(DB_PATH)
    
    # Process Lok Sabha data
    ls_file = os.path.join(LS_DIR, "loksabha_data.csv")
    if os.path.exists(ls_file):
        print(f"Processing {ls_file}")
        df_ls = pd.read_csv(ls_file)
        
        # Clean column names (e.g., lowercasing, replacing spaces with underscores)
        df_ls.columns = [c.strip().lower().replace(" ", "_") for c in df_ls.columns]
        
        # Handle missing values
        df_ls.fillna(0, inplace=True)
        
        # Load into DuckDB
        conn.execute("CREATE TABLE IF NOT EXISTS loksabha_expenditure AS SELECT * FROM df_ls")
        # To handle updates if table already exists, a robust ETL would drop/replace or upsert.
        conn.execute("CREATE OR REPLACE TABLE loksabha_expenditure AS SELECT * FROM df_ls")
        print("Lok Sabha data ingested successfully.")
    
    # Process Rajya Sabha data
    rs_file = os.path.join(RS_DIR, "rajyasabha_data.csv")
    if os.path.exists(rs_file):
        print(f"Processing {rs_file}")
        df_rs = pd.read_csv(rs_file)
        df_rs.columns = [c.strip().lower().replace(" ", "_") for c in df_rs.columns]
        df_rs.fillna(0, inplace=True)
        
        conn.execute("CREATE OR REPLACE TABLE rajyasabha_expenditure AS SELECT * FROM df_rs")
        print("Rajya Sabha data ingested successfully.")

    conn.close()
    print("ETL Pipeline completed.")

if __name__ == "__main__":
    run_etl()
