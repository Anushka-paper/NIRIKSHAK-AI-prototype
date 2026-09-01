import pandas as pd
from sqlalchemy import create_engine
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'app', 'nirikshak.db'))
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL)

RAW_DIR = os.path.join(os.path.dirname(__file__), 'raw_csvs')

def load_data():
    files = {
        "geography": "Geography.csv",
        "mp_master": "MP_Master.csv",
        "vendor_master": "Vendor_Master.csv",
        "ida_master": "IDA_Master.csv",
        "works_recommended": "Works_Recommended.csv",
        "works_sanctioned": "Works_Sanctioned.csv",
        "expenditure": "Expenditure.csv",
        "works_completed": "Works_Completed.csv",
        # We don't load Ground_Truth.csv into the main schema to keep it isolated for eval
    }
    
    with engine.begin() as conn:
        for table_name, file_name in files.items():
            file_path = os.path.join(RAW_DIR, file_name)
            if os.path.exists(file_path):
                print(f"Loading {file_name} into table {table_name}...")
                df = pd.read_csv(file_path)
                df.to_sql(table_name, conn, if_exists='append', index=False)
            else:
                print(f"Warning: {file_path} not found.")

if __name__ == "__main__":
    print("Starting data seed...")
    try:
        load_data()
        print("Data seed complete.")
    except Exception as e:
        print(f"Error seeding data: {e}")
        print("Make sure the PostgreSQL database is running via docker-compose.")
