import os
import re
import glob
import pandas as pd
from data_pipeline.cleaning.audit import CleaningAuditLogger
from data_pipeline.cleaning.encoding import clean_encoding
from data_pipeline.cleaning.whitespace import clean_whitespace
from data_pipeline.cleaning.nulls import clean_null_value
from data_pipeline.cleaning.numeric import clean_numeric_val
from data_pipeline.cleaning.dates import clean_date_val
from data_pipeline.cleaning.metadata import is_grand_total_row, is_repeated_header_row
from data_pipeline.cleaning.malformed_records import QuarantineManager

def normalize_col_name(col):
    c = clean_whitespace(str(col)).lower()
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
        
        cleaned_rows = []
        blank_rows_count = 0
        footer_rows_count = 0
        repeated_headers_count = 0
        
        for idx, row in df_raw.iterrows():
            source_row_num = idx + 2  # 1-based header + 1-based index
            
            # 1. Blank row check
            if row.dropna().empty or not ''.join(row.fillna('').values).strip():
                blank_rows_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", "", "", "REMOVE_BLANK_ROW", "All fields empty")
                continue
                
            # 2. Metadata / Grand Total footer check
            if is_grand_total_row(row):
                footer_rows_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.values), "", "STRIP_FOOTER_ROW", "Grand Total summary line")
                continue
                
            # 3. Repeated header check
            if is_repeated_header_row(row, raw_columns):
                repeated_headers_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.values), "", "REMOVE_REPEATED_HEADER", "Inline header repetition")
                continue

            cleaned_record = {
                "source_house": self.house_name,
                "source_file": filename,
                "source_row_number": source_row_num
            }
            
            is_malformed = False
            malformed_reason = ""
            
            for orig_col in raw_columns:
                norm_col = clean_col_map[orig_col]
                orig_val = row[orig_col]
                
                # Whitespace & Encoding
                c_val = clean_null_value(orig_val)
                
                if c_val is not None:
                    # Detect if date column
                    if "date" in norm_col or "completion" in norm_col or "consent" in norm_col:
                        date_res, is_valid_date = clean_date_val(c_val)
                        if not is_valid_date:
                            is_malformed = True
                            malformed_reason = f"Invalid date in column {norm_col}: '{orig_val}'"
                        c_val = date_res
                        
                    # Detect if numeric/currency column
                    elif "amount" in norm_col or "limit" in norm_col or "disbursed" in norm_col:
                        num_res, is_valid_num = clean_numeric_val(c_val, norm_col)
                        if not is_valid_num:
                            is_malformed = True
                            malformed_reason = f"Invalid numeric value in column {norm_col}: '{orig_val}'"
                        c_val = num_res
                        
                    if orig_val != c_val and not (pd.isna(orig_val) and c_val is None):
                        self.audit_logger.log_action(
                            filename, source_row_num, norm_col, orig_val, c_val, "CLEAN_VALUE", "Encoding/Whitespace/Null/Type coercion"
                        )
                        
                cleaned_record[norm_col] = c_val
                
            if is_malformed:
                self.quarantine_mgr.add_quarantine(filename, source_row_num, row.to_dict(), malformed_reason)
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.to_dict()), "", "QUARANTINE_RECORD", malformed_reason)
            else:
                cleaned_rows.append(cleaned_record)
                
        df_clean = pd.DataFrame(cleaned_rows)
        output_path = os.path.join(self.cleaned_dir, f"clean_{dataset_type}.csv")
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        
        self.quarantine_mgr.save_quarantine(dataset_type)
        
        metrics = {
            "dataset": dataset_type,
            "raw_rows": len(df_raw),
            "clean_rows": len(df_clean),
            "blank_rows_removed": blank_rows_count,
            "footer_rows_stripped": footer_rows_count,
            "repeated_headers_removed": repeated_headers_count,
            "quarantined_rows": len(self.quarantine_mgr.quarantined_records)
        }
        return metrics

with open("data_pipeline/cleaning/base_cleaner.py", "w", encoding="utf-8") as out:
    out.write('''import os
import re
import glob
import pandas as pd
from data_pipeline.cleaning.audit import CleaningAuditLogger
from data_pipeline.cleaning.encoding import clean_encoding
from data_pipeline.cleaning.whitespace import clean_whitespace
from data_pipeline.cleaning.nulls import clean_null_value
from data_pipeline.cleaning.numeric import clean_numeric_val
from data_pipeline.cleaning.dates import clean_date_val
from data_pipeline.cleaning.metadata import is_grand_total_row, is_repeated_header_row
from data_pipeline.cleaning.malformed_records import QuarantineManager

def normalize_col_name(col):
    c = clean_whitespace(str(col)).lower()
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
        
        cleaned_rows = []
        blank_rows_count = 0
        footer_rows_count = 0
        repeated_headers_count = 0
        
        for idx, row in df_raw.iterrows():
            source_row_num = idx + 2
            
            if row.dropna().empty or not ''.join(row.fillna('').values).strip():
                blank_rows_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", "", "", "REMOVE_BLANK_ROW", "All fields empty")
                continue
                
            if is_grand_total_row(row):
                footer_rows_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.values), "", "STRIP_FOOTER_ROW", "Grand Total summary line")
                continue
                
            if is_repeated_header_row(row, raw_columns):
                repeated_headers_count += 1
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.values), "", "REMOVE_REPEATED_HEADER", "Inline header repetition")
                continue

            cleaned_record = {
                "source_house": self.house_name,
                "source_file": filename,
                "source_row_number": source_row_num
            }
            
            is_malformed = False
            malformed_reason = ""
            
            for orig_col in raw_columns:
                norm_col = clean_col_map[orig_col]
                orig_val = row[orig_col]
                
                c_val = clean_null_value(orig_val)
                
                if c_val is not None:
                    if "date" in norm_col or "completion" in norm_col or "consent" in norm_col:
                        date_res, is_valid_date = clean_date_val(c_val)
                        if not is_valid_date:
                            is_malformed = True
                            malformed_reason = f"Invalid date in column {norm_col}: '{orig_val}'"
                        c_val = date_res
                        
                    elif "amount" in norm_col or "limit" in norm_col or "disbursed" in norm_col:
                        num_res, is_valid_num = clean_numeric_val(c_val, norm_col)
                        if not is_valid_num:
                            is_malformed = True
                            malformed_reason = f"Invalid numeric value in column {norm_col}: '{orig_val}'"
                        c_val = num_res
                        
                    if orig_val != c_val and not (pd.isna(orig_val) and c_val is None):
                        self.audit_logger.log_action(
                            filename, source_row_num, norm_col, orig_val, c_val, "CLEAN_VALUE", "Encoding/Whitespace/Null/Type coercion"
                        )
                        
                cleaned_record[norm_col] = c_val
                
            if is_malformed:
                self.quarantine_mgr.add_quarantine(filename, source_row_num, row.to_dict(), malformed_reason)
                self.audit_logger.log_action(filename, source_row_num, "ROW", str(row.to_dict()), "", "QUARANTINE_RECORD", malformed_reason)
            else:
                cleaned_rows.append(cleaned_record)
                
        df_clean = pd.DataFrame(cleaned_rows)
        output_path = os.path.join(self.cleaned_dir, f"clean_{dataset_type}.csv")
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        
        self.quarantine_mgr.save_quarantine(dataset_type)
        
        metrics = {
            "dataset": dataset_type,
            "raw_rows": len(df_raw),
            "clean_rows": len(df_clean),
            "blank_rows_removed": blank_rows_count,
            "footer_rows_stripped": footer_rows_count,
            "repeated_headers_removed": repeated_headers_count,
            "quarantined_rows": len(self.quarantine_mgr.quarantined_records)
        }
        return metrics
''')
print("Created data_pipeline/cleaning/base_cleaner.py!")
