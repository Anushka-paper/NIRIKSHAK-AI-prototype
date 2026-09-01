import os
import sys
import glob
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.models import (
    Base, MPMaster, MPAlias, Geography, IDAMaster, VendorMaster, VendorAlias,
    WorkRecommended, WorkSanctioned, Expenditure, WorkCompleted, CalamityConsent, Allocation
)
from ingestion.ingest_real_esakshi import ingest_dataset

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs'))
rs_dir = os.path.join(BASE_DIR, 'RS_DATASET')

print("Starting ingestion for Rajya Sabha Dataset...")
ingest_dataset("Rajya Sabha", rs_dir)
print("Finished Rajya Sabha Ingestion.")

