"""
Report and Summary Generator for Entity Resolution.
Generates JSON audit reports and summary CSV files.
"""

import json
from pathlib import Path
import pandas as pd

class ReportGenerator:
    """
    Exports summary statistics and audit reports for Entity Resolution.
    """

    def generate_report(self, summary_data: dict, output_dir: Path) -> Path:
        """
        Saves entity_resolution_report.json.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "entity_resolution_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
        return report_path

    def generate_summary_csv(self, pair_stats: list[dict], output_dir: Path) -> Path:
        """
        Saves entity_resolution_summary.csv.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "entity_resolution_summary.csv"
        df = pd.DataFrame(pair_stats)
        df.to_csv(summary_path, index=False)
        return summary_path

