import pandas as pd
import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import select

class BaseCSVLoader:
    def __init__(self, db: Session, target_model, unique_key_col: str):
        self.db = db
        self.target_model = target_model
        self.unique_key_col = unique_key_col

    def hash_row(self, row: pd.Series) -> str:
        """
        Computes a stable SHA-256 hash of a dictionary/Series representing a row.
        """
        # Convert to dictionary, sorting keys to ensure stability
        row_dict = row.to_dict()
        # Handle nan/NaT
        clean_dict = {k: (v if pd.notna(v) else None) for k, v in row_dict.items()}
        
        row_str = json.dumps(clean_dict, sort_keys=True, default=str)
        return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

    def add_hashes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds a source_row_hash column to the dataframe."""
        df = df.copy()
        df['source_row_hash'] = df.apply(self.hash_row, axis=1)
        return df

    def filter_changed_rows(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compares incoming rows with the database and splits them into:
        1. Changed or new rows (to be processed)
        2. Unchanged rows (to be skipped)
        """
        if df.empty:
            return df, pd.DataFrame()
            
        incoming_hashes = df[['source_row_hash', self.unique_key_col]].copy()
        
        # We need the existing hashes from the database for the keys present in the batch
        keys = incoming_hashes[self.unique_key_col].tolist()
        
        # Depending on the target_model, we fetch existing hashes
        # This assumes the target_model has `source_row_hash` and the attribute named by unique_key_col
        key_attr = getattr(self.target_model, self.unique_key_col, None)
        if not key_attr:
            # If target model doesn't have this key, we process everything (e.g. initial load without a good PK match)
            return df, pd.DataFrame()
            
        stmt = select(key_attr, self.target_model.source_row_hash).where(key_attr.in_(keys))
        existing_rows = self.db.execute(stmt).all()
        
        existing_hash_map = {getattr(row, self.unique_key_col): row.source_row_hash for row in existing_rows}
        
        changed_mask = df.apply(
            lambda r: existing_hash_map.get(r[self.unique_key_col]) != r['source_row_hash'], 
            axis=1
        )
        
        return df[changed_mask], df[~changed_mask]

    def load(self, file_path: str):
        """
        Main entry point for loading a file. Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement load()")
