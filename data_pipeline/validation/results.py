import datetime
import os
import pandas as pd

class ValidationResultLogger:
    def __init__(self):
        self.results = []

    def log_result(self, source_house, dataset, source_file, source_row, column_name, rule_id, rule_name, severity, status, observed_value, expected_condition, message):
        self.results.append({
            "validation_id": f"VAL_{len(self.results) + 1:06d}",
            "source_house": source_house,
            "dataset": dataset,
            "source_file": source_file,
            "source_row": source_row,
            "column_name": column_name,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "severity": severity,
            "status": status,
            "observed_value": str(observed_value),
            "expected_condition": expected_condition,
            "message": message,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pipeline_version": "1.0.0"
        })

    def get_df(self):
        return pd.DataFrame(self.results)

    def save_to_csv(self, output_path):
        if not self.results:
            return
        df = pd.DataFrame(self.results)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8")
