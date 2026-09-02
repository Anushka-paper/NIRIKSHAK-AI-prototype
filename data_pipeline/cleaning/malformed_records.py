import json
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
