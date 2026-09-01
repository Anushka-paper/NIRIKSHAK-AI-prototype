import os
import re
import pandas as pd
from data_pipeline.cleaning.audit import CleaningAuditLogger
from data_pipeline.cleaning.malformed_records import QuarantineManager

NULL_PATTERNS = {'n/a', 'na', 'null', 'none', 'nan', 'not available', 'blank', '', 'n.a.'}

def normalize_col_name(col):
    c = str(col).strip().lower()
    c = re.sub(r'[\(?\)\.\'-]', '', c)
    c = re.sub(r'\s+', '_', c).strip('_')
    return c

class BaseCleaner:
    def __init__(self, house_name, raw_dir, cleaned_dir, quarantine_dir):
        self.house_name = house_name
        self.raw_dir = raw_dir
        self.cleaned_dir = cleaned_dir
        self.quarantine_dir = quarantine_dir
        self.audit_logger = CleaningAuditLogger(house_name=house_name)
        self.quarantine_mgr = QuarantineManager(house_name=house_name, quarantine_dir=quarantine_dir)
        
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def process_file(self, filepath, dataset_type):
        filename = os.path.basename(filepath)
        print(f"[{self.house_name}] Cleaning dataset: {filename}...")
        
        try:
            df_raw = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str, low_memory=False)
        except Exception:
            df_raw = pd.read_csv(filepath, encoding='latin1', dtype=str, low_memory=False)

        raw_columns = list(df_raw.columns)
        clean_col_map = {col: normalize_col_name(col) for col in raw_columns}
        
        # 1. Blank row removal
        non_blank_mask = df_raw.dropna(how='all').index
        blank_rows_count = len(df_raw) - len(non_blank_mask)
        df_filtered = df_raw.loc[non_blank_mask].copy()
        
        # 2. Strip Footer Row (Grand Total)
        footer_rows_count = 0
        if not df_filtered.empty:
            last_row_str = ' '.join(df_filtered.iloc[-1].fillna('').astype(str).values).lower()
            if 'grand total' in last_row_str or 'total:' in last_row_str:
                footer_rows_count = 1
                df_filtered = df_filtered.iloc[:-1].copy()

        # 3. Add Source Lineage Attributes
        df_filtered.insert(0, 'source_house', self.house_name)
        df_filtered.insert(1, 'source_file', filename)
        df_filtered.insert(2, 'source_row_number', df_filtered.index + 2)

        # 4. Clean Columns & Rename
        rename_dict = {col: clean_col_map[col] for col in raw_columns}
        df_clean = df_filtered.rename(columns=rename_dict)

        # Vectorized Column Transformations
        for col in list(clean_col_map.values()):
            if col in df_clean.columns:
                s = df_clean[col].fillna('').astype(str)
                # UTF-8 BOM, \xa0, Windows-1252 fixes
                s = s.str.replace('\ufeff', '', regex=False).str.replace('\xa0', ' ', regex=False).str.replace('–', '-', regex=False).str.replace('é', 'e', regex=False)
                s = s.str.strip()
                s_lower = s.str.lower()
                is_null = s_lower.isin(NULL_PATTERNS)
                
                if 'date' in col or 'completion' in col or 'consent' in col:
                    # Convert to ISO %Y-%m-%d
                    parsed_dates = pd.to_datetime(s.where(~is_null), dayfirst=True, errors='coerce')
                    s_final = parsed_dates.dt.strftime('%Y-%m-%d').where(parsed_dates.notna(), None)
                elif 'amount' in col or 'limit' in col or 'disbursed' in col:
                    num_str = s.str.replace(r'[^0-9.-]', '', regex=True)
                    parsed_nums = pd.to_numeric(num_str.where(~is_null), errors='coerce')
                    s_final = parsed_nums.where(parsed_nums.notna(), None)
                else:
                    s_final = s.where(~is_null, None)

                df_clean[col] = s_final

        output_path = os.path.join(self.cleaned_dir, f"clean_{dataset_type}.csv")
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        
        self.audit_logger.log_action(filename, 0, "DATASET", str(len(df_raw)), str(len(df_clean)), "VECTORIZED_CLEAN", f"Processed {dataset_type} dataset")
        
        metrics = {
            "dataset": dataset_type,
            "raw_rows": len(df_raw),
            "clean_rows": len(df_clean),
            "blank_rows_removed": blank_rows_count,
            "footer_rows_stripped": footer_rows_count,
            "repeated_headers_removed": 0,
            "quarantined_rows": 0
        }
        return metrics

with open("data_pipeline/cleaning/base_cleaner.py", "w", encoding="utf-8") as out:
    out.write('''import os
import re
import pandas as pd
from data_pipeline.cleaning.audit import CleaningAuditLogger
from data_pipeline.cleaning.malformed_records import QuarantineManager

NULL_PATTERNS = {'n/a', 'na', 'null', 'none', 'nan', 'not available', 'blank', '', 'n.a.'}

def normalize_col_name(col):
    c = str(col).strip().lower()
    c = re.sub(r'[\\(?\\)\\.\\\'-]', '', c)
    c = re.sub(r'\\s+', '_', c).strip('_')
    return c

class BaseCleaner:
    def __init__(self, house_name, raw_dir, cleaned_dir, quarantine_dir):
        self.house_name = house_name
        self.raw_dir = raw_dir
        self.cleaned_dir = cleaned_dir
        self.quarantine_dir = quarantine_dir
        self.audit_logger = CleaningAuditLogger(house_name=house_name)
        self.quarantine_mgr = QuarantineManager(house_name=house_name, quarantine_dir=quarantine_dir)
        
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def process_file(self, filepath, dataset_type):
        filename = os.path.basename(filepath)
        print(f"[{self.house_name}] Cleaning dataset: {filename}...")
        
        try:
            df_raw = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str, low_memory=False)
        except Exception:
            df_raw = pd.read_csv(filepath, encoding='latin1', dtype=str, low_memory=False)

        raw_columns = list(df_raw.columns)
        clean_col_map = {col: normalize_col_name(col) for col in raw_columns}
        
        non_blank_mask = df_raw.dropna(how='all').index
        blank_rows_count = len(df_raw) - len(non_blank_mask)
        df_filtered = df_raw.loc[non_blank_mask].copy()
        
        footer_rows_count = 0
        if not df_filtered.empty:
            last_row_str = ' '.join(df_filtered.iloc[-1].fillna('').astype(str).values).lower()
            if 'grand total' in last_row_str or 'total:' in last_row_str:
                footer_rows_count = 1
                df_filtered = df_filtered.iloc[:-1].copy()

        df_filtered.insert(0, 'source_house', self.house_name)
        df_filtered.insert(1, 'source_file', filename)
        df_filtered.insert(2, 'source_row_number', df_filtered.index + 2)

        rename_dict = {col: clean_col_map[col] for col in raw_columns}
        df_clean = df_filtered.rename(columns=rename_dict)

        for col in list(clean_col_map.values()):
            if col in df_clean.columns:
                s = df_clean[col].fillna('').astype(str)
                s = s.str.replace('\\ufeff', '', regex=False).str.replace('\\xa0', ' ', regex=False).str.replace('–', '-', regex=False).str.replace('é', 'e', regex=False)
                s = s.str.strip()
                s_lower = s.str.lower()
                is_null = s_lower.isin(NULL_PATTERNS)
                
                if 'date' in col or 'completion' in col or 'consent' in col:
                    parsed_dates = pd.to_datetime(s.where(~is_null), dayfirst=True, errors='coerce')
                    s_final = parsed_dates.dt.strftime('%Y-%m-%d').where(parsed_dates.notna(), None)
                elif 'amount' in col or 'limit' in col or 'disbursed' in col:
                    num_str = s.str.replace(r'[^0-9.-]', '', regex=True)
                    parsed_nums = pd.to_numeric(num_str.where(~is_null), errors='coerce')
                    s_final = parsed_nums.where(parsed_nums.notna(), None)
                else:
                    s_final = s.where(~is_null, None)

                df_clean[col] = s_final

        output_path = os.path.join(self.cleaned_dir, f"clean_{dataset_type}.csv")
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        
        self.audit_logger.log_action(filename, 0, "DATASET", str(len(df_raw)), str(len(df_clean)), "VECTORIZED_CLEAN", f"Processed {dataset_type} dataset")
        
        metrics = {
            "dataset": dataset_type,
            "raw_rows": len(df_raw),
            "clean_rows": len(df_clean),
            "blank_rows_removed": blank_rows_count,
            "footer_rows_stripped": footer_rows_count,
            "repeated_headers_removed": 0,
            "quarantined_rows": 0
        }
        return metrics
''')

print("Created high-performance base_cleaner.py!")
