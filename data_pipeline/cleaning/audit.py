import datetime
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
