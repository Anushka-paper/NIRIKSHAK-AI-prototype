import os
import glob
import pandas as pd
from data_pipeline.validation.results import ValidationResultLogger
from data_pipeline.validation.config import RULE_CONFIGS
from data_pipeline.validation.schemas.lok_sabha import LOK_SABHA_SCHEMAS
from data_pipeline.validation.schemas.rajya_sabha import RAJYA_SABHA_SCHEMAS
from data_pipeline.validation.quality_score import calculate_quality_score
from data_pipeline.validation.rules.schema import validate_schema
from data_pipeline.validation.rules.types import validate_numeric_columns
from data_pipeline.validation.rules.nulls import profile_nulls
from data_pipeline.validation.rules.identifiers import validate_work_ids
from data_pipeline.validation.rules.currency import validate_currency_rules
from data_pipeline.validation.rules.dates import validate_iso_dates
from data_pipeline.validation.rules.date_sequences import validate_date_sequence
from data_pipeline.validation.rules.geography import validate_geography
from data_pipeline.validation.rules.business import validate_business_rules

class ValidationEngine:
    def __init__(self, house_name, cleaned_dir):
        self.house_name = house_name
        self.cleaned_dir = cleaned_dir
        self.logger = ValidationResultLogger()
        self.schemas = LOK_SABHA_SCHEMAS if house_name == "LOK_SABHA" else RAJYA_SABHA_SCHEMAS

    def validate_dataset(self, dataset_name, df):
        filename = f"clean_{dataset_name}.csv"
        schema_cfg = self.schemas.get(dataset_name, {})
        req_cols = schema_cfg.get("required", [])
        
        errors = 0
        warnings = 0
        
        # 1. Schema Validation (SCH-001)
        missing_req = validate_schema(df, req_cols)
        if missing_req:
            errors += len(missing_req)
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, "COLUMNS", "SCH-001",
                "Required Columns Check", "ERROR", "FAIL", str(missing_req),
                f"Must contain columns {req_cols}", f"Missing required columns: {missing_req}"
            )

        # 2. Type Checks (TYP-001, TYP-002)
        invalid_nums = validate_numeric_columns(df)
        if invalid_nums:
            errors += len(invalid_nums)
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, str(invalid_nums), "TYP-001",
                "Numeric Data Type Check", "ERROR", "FAIL", str(invalid_nums),
                "Numeric columns parseable as float", f"Corrupted text in numeric columns: {invalid_nums}"
            )

        invalid_dates = validate_iso_dates(df)
        for d_col, count in invalid_dates.items():
            errors += count
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, d_col, "TYP-002",
                "ISO Date Format Check", "ERROR", "FAIL", str(count),
                "ISO YYYY-MM-DD", f"Found {count} non-ISO date strings in {d_col}"
            )

        # 3. Null Profiling (NUL-001)
        null_prof = profile_nulls(df, req_cols)
        for col, prof in null_prof.items():
            if prof["classification"] == "REQUIRED" and prof["null_count"] > 0:
                errors += prof["null_count"]
                self.logger.log_result(
                    self.house_name, dataset_name, filename, 0, col, "NUL-001",
                    "Required Field Completeness", "ERROR", "FAIL", str(prof["null_count"]),
                    f"{col} must be non-null", f"Required column {col} has {prof['null_count']} null values"
                )

        # 4. Identifier Checks (ID-001)
        blank_wids, malformed_wids = validate_work_ids(df)
        if malformed_wids > 0:
            warnings += malformed_wids
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, "work_id", "ID-001",
                "Work ID Format Validation", "WARNING", "WARNING", str(malformed_wids),
                "work_id starts with WS/", f"Found {malformed_wids} non-standard work_ids"
            )

        # 5. Currency Non-Negativity & Large Amount Warnings (CUR-001, CUR-002)
        negs, larges = validate_currency_rules(df)
        for col, count in negs.items():
            errors += count
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, col, "CUR-001",
                "Non-Negative Currency", "ERROR", "FAIL", str(count),
                f"{col} >= 0", f"Found {count} negative monetary values in {col}"
            )
        for col, count in larges.items():
            warnings += count
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, col, "CUR-002",
                "Suspicious Large Amount Warning", "WARNING", "WARNING", str(count),
                f"{col} <= 100 Cr", f"Found {count} records exceeding ₹ 100 Cr limit in {col}"
            )

        # 6. Chronological Date Sequences (DAT-001)
        seq_errors = validate_date_sequence(df)
        if seq_errors > 0:
            errors += seq_errors
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, "sanction_date", "DAT-001",
                "Chronological Sequence Check", "ERROR", "FAIL", str(seq_errors),
                "recommended_date <= sanction_date", f"Found {seq_errors} works where sanction_date preceded recommended_date"
            )

        # 7. Geographic & Business Rules (GEO-001, BUS-001)
        m_state, m_const = validate_geography(df, self.house_name)
        m_comp_date = validate_business_rules(df)
        if m_comp_date > 0:
            warnings += m_comp_date
            self.logger.log_result(
                self.house_name, dataset_name, filename, 0, "completion_date", "BUS-001",
                "Completed Status Work Check", "WARNING", "WARNING", str(m_comp_date),
                "completion_date present when status COMPLETED", f"Found {m_comp_date} completed works missing completion_date"
            )

        status = "VALID"
        if errors > 0:
            status = "INVALID"
        elif warnings > 0:
            status = "VALID_WITH_WARNING"

        return {
            "dataset": dataset_name,
            "rows": len(df),
            "errors": errors,
            "warnings": warnings,
            "status": status,
            "null_profile": null_prof
        }

    def validate_all(self):
        print(f"[{self.house_name}] Running Modular Validation Engine...")
        datasets_metrics = {}
        total_rows = 0
        total_errors = 0
        total_warnings = 0
        
        files = glob.glob(os.path.join(self.cleaned_dir, "clean_*.csv"))
        for f in files:
            ds_name = os.path.basename(f).replace("clean_", "").replace(".csv", "")
            df = pd.read_csv(f, low_memory=False)
            res = self.validate_dataset(ds_name, df)
            datasets_metrics[ds_name] = res
            total_rows += res["rows"]
            total_errors += res["errors"]
            total_warnings += res["warnings"]

        q_score = calculate_quality_score(total_rows, total_errors, total_warnings)
        
        res_log_path = os.path.join("data", "reports", f"{self.house_name.lower()}_validation_results.csv")
        self.logger.save_to_csv(res_log_path)
        
        return {
            "house": self.house_name,
            "total_rows": total_rows,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "quality_score": q_score,
            "datasets": datasets_metrics
        }
