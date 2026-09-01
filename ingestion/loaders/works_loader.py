import pandas as pd
from sqlalchemy.orm import Session
from db.models import WorkRecommended
from ingestion.loaders.csv_loader import BaseCSVLoader
from ingestion.cleaning.headers import normalize_header
from ingestion.cleaning.currency import clean_currency_to_paise
from ingestion.cleaning.dates import standardize_date
from ingestion.entity_resolution.work_id_parser import parse_work_id
from ingestion.entity_resolution.mp_resolver import resolve_mp

class WorksRecommendedLoader(BaseCSVLoader):
    def __init__(self, db: Session):
        super().__init__(db, WorkRecommended, 'work_id_raw')

    def load(self, file_path: str):
        df = pd.read_csv(file_path)
        
        # 1. Normalize headers
        df.columns = [normalize_header(c) for c in df.columns]
        
        # 2. Add hashes for incremental check
        df = self.add_hashes(df)
        
        # 3. Filter unchanged rows
        changed_df, _ = self.filter_changed_rows(df)
        if changed_df.empty:
            return {"processed": 0, "quarantined": 0}
            
        processed_count = 0
        quarantine_count = 0
        
        # 4. Process changed rows
        for _, row in changed_df.iterrows():
            try:
                # Cleaning & Entity Resolution
                work_id_raw = str(row.get('work_id_raw', ''))
                canonical_id = parse_work_id(work_id_raw)
                
                # In real data we might not have MP ID directly, so we'd resolve by name.
                # Since our synthetic generator outputs mp_id directly for ease, we simulate resolution
                mp_id = row.get('mp_id')
                if not mp_id and 'mp_name' in row:
                    mp_id, score = resolve_mp(self.db, row['mp_name'])
                    if mp_id is None:
                        # Queue for review (quarantine for now)
                        quarantine_count += 1
                        continue
                
                rec_amount = clean_currency_to_paise(row.get('recommended_amount', 0))
                rec_date = standardize_date(row.get('recommendation_date'))
                
                # Upsert to DB
                work = self.db.query(WorkRecommended).filter(
                    WorkRecommended.work_id_raw == work_id_raw
                ).first()
                
                if not work:
                    work = WorkRecommended(work_id_raw=work_id_raw)
                    self.db.add(work)
                    
                work.mp_id = mp_id
                work.ida_id = row.get('ida_id')
                work.category = row.get('category')
                work.description = row.get('description')
                work.recommended_amount = rec_amount
                work.recommendation_date = rec_date
                work.source_row_hash = row['source_row_hash']
                
                processed_count += 1
                
            except Exception as e:
                # Log quarantine
                quarantine_count += 1
                
        self.db.commit()
        return {"processed": processed_count, "quarantined": quarantine_count}
