import os
import pandas as pd

class IntegrationExceptionLogger:
    def __init__(self):
        self.exceptions = []

    def log_exception(self, source_dataset, source_row_id, source_work_id, candidate_key, strategy, reason, status):
        self.exceptions.append({
            "source_dataset": source_dataset,
            "source_row_id": source_row_id,
            "source_work_id": str(source_work_id),
            "candidate_join_key": str(candidate_key),
            "failed_join_strategy": strategy,
            "reason": reason,
            "integration_status": status,
            "timestamp": pd.Timestamp.now().isoformat()
        })

    def save_to_csv(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df = pd.DataFrame(self.exceptions) if self.exceptions else pd.DataFrame(columns=["source_dataset", "source_row_id", "source_work_id", "candidate_join_key", "failed_join_strategy", "reason", "integration_status", "timestamp"])
        df.to_csv(output_path, index=False, encoding="utf-8")
