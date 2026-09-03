"""
Dynamic Data Cleaner for NIRIKSHAK-AI.
Safely remediates data quality issues:
- Placeholder null token remediation ('NA', 'N/A', '-', '--', 'None', 'null', 'undefined' -> None)
- Whitespace stripping and internal whitespace collapsing
- Detection and removal of summary/total rows with audit logging
- Duplicate record detection and removal with audit logging
- Full transformation audit trail
"""

import re
import unicodedata
import pandas as pd
import numpy as np

SUMMARY_ROW_PATTERN = r'(?i)^(grand\s+total|total|summary)[\:\s]*$'
NULL_TOKENS = {"", " ", "na", "n/a", "na/", "/na", "null", "none", "-", "--", "not available", "nil", "n.a.", "undefined"}

class DataCleaner:
    """
    Dynamic Data Cleaning Engine.
    Cleans datasets without deleting valid data and maintains an audit trail.
    """

    def __init__(self, remove_summary_rows: bool = True, remove_duplicate_rows: bool = True):
        self.remove_summary_rows = remove_summary_rows
        self.remove_duplicate_rows = remove_duplicate_rows

    def clean(self, df: pd.DataFrame) -> dict:
        """
        Executes dynamic cleaning on DataFrame.
        Returns dict with cleaned 'data' (pd.DataFrame) and 'audit_trail' (dict).
        """
        if df.empty:
            return {
                "data": df.copy(),
                "audit_trail": {
                    "original_rows": 0,
                    "cleaned_rows": 0,
                    "transformations": []
                }
            }

        df_cleaned = df.copy()
        initial_rows = len(df_cleaned)
        transformations = []

        # 1. Summary / Total Row Segregation
        if self.remove_summary_rows:
            summary_mask = pd.Series(False, index=df_cleaned.index)
            for col in df_cleaned.columns:
                if df_cleaned[col].dtype == object or pd.api.types.is_string_dtype(df_cleaned[col]):
                    matches = df_cleaned[col].astype(str).str.strip().str.match(SUMMARY_ROW_PATTERN, na=False)
                    summary_mask = summary_mask | matches

            summary_count = int(summary_mask.sum())
            if summary_count > 0:
                summary_examples = df_cleaned[summary_mask].head(3).to_dict(orient="records")
                df_cleaned = df_cleaned[~summary_mask].reset_index(drop=True)
                transformations.append({
                    "operation": "summary_row_removal",
                    "column": None,
                    "affected_rows": summary_count,
                    "reason": "Removed aggregate/total rows that pollute record-level analysis",
                    "examples": summary_examples
                })

        # 2. Duplicate Rows Removal
        if self.remove_duplicate_rows:
            duplicate_count = int(df_cleaned.duplicated().sum())
            if duplicate_count > 0:
                df_cleaned = df_cleaned.drop_duplicates().reset_index(drop=True)
                transformations.append({
                    "operation": "duplicate_row_removal",
                    "column": None,
                    "affected_rows": duplicate_count,
                    "reason": "Removed exact duplicate records",
                    "examples": []
                })

        # 3. Column-Level String Cleaning & Null-Token Remediation
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype == object or pd.api.types.is_string_dtype(df_cleaned[col]):
                series = df_cleaned[col]
                cleaned_vals = []
                null_tokens_replaced = 0
                whitespace_trimmed = 0
                before_after_samples = []

                for val in series:
                    if pd.isna(val) or val is None:
                        cleaned_vals.append(val)
                        continue

                    val_str = str(val)
                    # Check for null tokens
                    if val_str.strip().lower() in NULL_TOKENS:
                        cleaned_vals.append(None)
                        null_tokens_replaced += 1
                        if len(before_after_samples) < 3:
                            before_after_samples.append({"before": val_str, "after": None})
                    else:
                        # Normalize unicode and whitespace
                        norm_val = unicodedata.normalize('NFKC', val_str)
                        norm_val = re.sub(r'\s+', ' ', norm_val).strip()
                        if norm_val != val_str:
                            whitespace_trimmed += 1
                        cleaned_vals.append(norm_val)

                if null_tokens_replaced > 0:
                    transformations.append({
                        "operation": "null_token_remediation",
                        "column": col,
                        "affected_rows": null_tokens_replaced,
                        "reason": f"Replaced placeholder null tokens ({list(NULL_TOKENS)[:4]}...) with standard nulls",
                        "examples": before_after_samples
                    })

                if whitespace_trimmed > 0:
                    transformations.append({
                        "operation": "whitespace_normalization",
                        "column": col,
                        "affected_rows": whitespace_trimmed,
                        "reason": "Trimmed leading/trailing spaces and collapsed multi-spaces",
                        "examples": []
                    })

                df_cleaned[col] = cleaned_vals

        final_rows = len(df_cleaned)
        return {
            "data": df_cleaned,
            "audit_trail": {
                "original_rows": initial_rows,
                "cleaned_rows": final_rows,
                "rows_removed": initial_rows - final_rows,
                "transformations": transformations
            }
        }

