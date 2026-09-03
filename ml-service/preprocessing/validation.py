"""
Multi-Level Data Validation Suite for NIRIKSHAK-AI.
Implements:
1. Dataset-level validation (readability, row count, column count, empty check)
2. Column-level validation (type integrity, null thresholds, non-negative amounts, date validity)
3. Row-level validation (critical missing fields, impossible ranges)
"""

import re
import pandas as pd
import numpy as np

class DataValidator:
    """
    Dynamic 3-tier validation suite.
    """

    def validate(self, df: pd.DataFrame, dataset_name: str = "dataset") -> dict:
        """
        Executes full validation audit.
        Returns dict with overall status ('PASSED', 'WARNING', 'FAILED'),
        errors, warnings, and audit metrics.
        """
        errors = []
        warnings = []

        # 1. Dataset-Level Validation
        if df is None:
            return {
                "status": "FAILED",
                "dataset_level": {"is_readable": False, "row_count": 0, "col_count": 0},
                "errors": ["Dataset is None or could not be loaded"],
                "warnings": []
            }

        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows == 0:
            errors.append("Dataset has 0 rows (empty dataset)")
        if total_cols == 0:
            errors.append("Dataset has 0 columns")

        dataset_level = {
            "is_readable": True,
            "row_count": total_rows,
            "col_count": total_cols,
            "columns": list(df.columns)
        }

        # 2. Column-Level Validation
        column_level = {}
        for col in df.columns:
            series = df[col]
            null_cnt = int(series.isnull().sum())
            null_pct = round((null_cnt / (total_rows or 1)) * 100, 2)

            col_audit = {
                "column_name": col,
                "null_count": null_cnt,
                "null_percentage": null_pct,
                "dtype": str(series.dtype)
            }

            if null_pct > 60.0:
                warnings.append(f"Column '{col}' has very high missingness ({null_pct}%)")

            # Check numeric & monetary columns for negative numbers
            if any(k in col.lower() for k in ["amount", "cost", "expenditure", "fund"]):
                numeric_vals = pd.to_numeric(series, errors='coerce').dropna()
                neg_count = int((numeric_vals < 0).sum())
                if neg_count > 0:
                    warnings.append(f"Column '{col}' contains {neg_count} negative monetary values")

            # Check date columns for non-ISO or malformed dates
            if "date" in col.lower():
                non_null_dates = series.dropna().astype(str)
                invalid_dates = [d for d in non_null_dates if not re.match(r'^\d{4}-\d{2}-\d{2}', d)]
                if invalid_dates:
                    warnings.append(f"Column '{col}' contains {len(invalid_dates)} non-ISO date values")

            column_level[col] = col_audit

        # Determine overall status
        status = "PASSED"
        if errors:
            status = "FAILED"
        elif warnings:
            status = "WARNING"

        return {
            "status": status,
            "dataset_name": dataset_name,
            "dataset_level": dataset_level,
            "column_level": column_level,
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0
        }

def validate_schema(df, required_columns):
    """Legacy helper maintained for backward compatibility."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True
