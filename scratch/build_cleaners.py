import os
import re
import json
import datetime
import pandas as pd

def save(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as out:
        out.write(content.strip() + '\n')
    print('Created:', path)

save('data_pipeline/__init__.py', '"""MPLADS Data Pipeline Package"""')
save('data_pipeline/cleaning/__init__.py', '"""MPLADS Data Cleaning Package"""')

save('data_pipeline/cleaning/audit.py', '''import datetime
import json
import os
import pandas as pd

class CleaningAuditLogger:
    def __init__(self, house_name="UNKNOWN"):
        self.house_name = house_name
        self.logs = []

    def log_action(self, source_file, source_row, column_name, original_value, cleaned_value, action, reason=""):
        self.logs.append({
            "source_house": self.house_name,
            "source_file": source_file,
            "source_row_number": source_row,
            "column_name": column_name,
            "original_value": str(original_value),
            "cleaned_value": str(cleaned_value),
            "cleaning_action": action,
            "reason": reason,
            "pipeline_version": "1.0.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def get_logs(self):
        return self.logs

    def save_to_csv(self, output_path):
        if not self.logs:
            return
        df = pd.DataFrame(self.logs)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8")
''')

save('data_pipeline/cleaning/encoding.py', '''def clean_encoding(val):
    if not isinstance(val, str):
        return val
    if val.startswith('\\ufeff'):
        val = val.lstrip('\\ufeff')
    val = val.replace('\\xa0', ' ')
    val = val.replace('–', '-').replace('é', 'e')
    return val
''')

save('data_pipeline/cleaning/whitespace.py', '''from data_pipeline.cleaning.encoding import clean_encoding

def clean_whitespace(val):
    if not isinstance(val, str):
        return val
    cleaned = clean_encoding(val)
    cleaned = cleaned.strip()
    cleaned = ' '.join(cleaned.split())
    return cleaned
''')

save('data_pipeline/cleaning/nulls.py', '''import pandas as pd
from data_pipeline.cleaning.whitespace import clean_whitespace

NULL_PATTERNS = {'n/a', 'na', 'null', 'none', 'nan', 'not available', 'blank', '', 'n.a.'}

def clean_null_value(val):
    if val is None or pd.isna(val):
        return None
    if isinstance(val, str):
        cleaned_str = clean_whitespace(val)
        if cleaned_str.lower() in NULL_PATTERNS:
            return None
        return cleaned_str
    return val
''')

save('data_pipeline/cleaning/numeric.py', '''import re
import pandas as pd

def clean_numeric_val(val, field_name="numeric_field"):
    if val is None or pd.isna(val):
        return None, True
    if isinstance(val, (int, float)):
        return float(val), True
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {'n/a', 'na', 'null', 'nan', 'none', '-'}:
        return None, True
        
    clean_str = re.sub(r'[^0-9.-]', '', val_str)
    try:
        num_val = float(clean_str)
        return num_val, True
    except ValueError:
        return None, False
''')

save('data_pipeline/cleaning/dates.py', '''import pandas as pd
from datetime import datetime

def clean_date_val(val):
    if val is None or pd.isna(val):
        return None, True
        
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {'n/a', 'na', 'null', 'nan', 'none', '-'}:
        return None, True
        
    if val_str.isdigit():
        try:
            excel_date = pd.to_datetime(int(val_str), unit='D', origin='1899-12-30')
            return excel_date.strftime('%Y-%m-%d'), True
        except Exception:
            pass

    date_formats = [
        '%d-%b-%Y', '%d-%B-%Y', '%d/%m/%Y', '%Y-%m-%d',
        '%d-%m-%Y', '%Y/%m/%d', '%d-%b-%y', '%d/%m/%y'
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(val_str, fmt)
            if 1950 <= parsed.year <= 2035:
                return parsed.strftime('%Y-%m-%d'), True
        except ValueError:
            continue
            
    try:
        parsed = pd.to_datetime(val_str, dayfirst=True, errors='raise')
        if 1950 <= parsed.year <= 2035:
            return parsed.strftime('%Y-%m-%d'), True
    except Exception:
        pass
        
    return None, False
''')

save('data_pipeline/cleaning/metadata.py', '''import pandas as pd

def is_grand_total_row(row):
    row_values_str = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
    return 'grand total' in row_values_str or 'total:' in row_values_str

def is_repeated_header_row(row, columns):
    row_vals = [str(v).strip().lower() for v in row.values]
    col_vals = [str(c).strip().lower() for c in columns]
    matches = sum(1 for r, c in zip(row_vals, col_vals) if r == c)
    return matches >= (len(columns) // 2)
''')

save('data_pipeline/cleaning/malformed_records.py', '''import json
import os

class QuarantineManager:
    def __init__(self, house_name, quarantine_dir):
        self.house_name = house_name
        self.quarantine_dir = quarantine_dir
        self.quarantined_records = []
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def add_quarantine(self, source_file, source_row, raw_record, reason):
        self.quarantined_records.append({
            "source_house": self.house_name,
            "source_file": source_file,
            "source_row_number": source_row,
            "raw_record": raw_record if isinstance(raw_record, dict) else str(raw_record),
            "quarantine_reason": reason
        })

    def save_quarantine(self, dataset_name):
        if not self.quarantined_records:
            return
        out_path = os.path.join(self.quarantine_dir, f"{dataset_name}_quarantine.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.quarantined_records, f, indent=2)
''')

save('data_pipeline/cleaning/validation.py', '''def validate_record_schema(record, source_house, dataset_type):
    if record.get('source_house') != source_house:
        return False, "Source house tag mismatch"
        
    if dataset_type == 'allocated_limit':
        if not record.get('honble_members_of_parliaments') and not record.get('honble_members_of_parliament'):
            return False, "Missing MP name"
    return True, "Valid"
''')

print("Created base utility files!")
