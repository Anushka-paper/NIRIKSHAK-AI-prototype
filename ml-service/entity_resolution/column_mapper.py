"""
Dynamic Semantic Column Mapper for Entity Resolution.
Detects semantic roles of columns regardless of naming variations.
"""

import re
import pandas as pd
from .config import SEMANTIC_COLUMN_ALIASES

class ColumnMapper:
    """
    Detects and maps arbitrary DataFrame column names to canonical entity keys.
    """

    def __init__(self, custom_aliases: dict = None):
        self.aliases = SEMANTIC_COLUMN_ALIASES.copy()
        if custom_aliases:
            self.aliases.update(custom_aliases)

    def detect_semantic_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Maps canonical semantic roles (e.g. 'work_id', 'mp_name', 'work_description')
        to the actual column names present in the DataFrame.
        """
        mapping = {}
        columns = list(df.columns)

        for canonical_role, patterns in self.aliases.items():
            for col in columns:
                clean_col = str(col).strip().lower()
                for pattern in patterns:
                    if re.search(pattern, clean_col):
                        if canonical_role not in mapping:
                            mapping[canonical_role] = col
                        break
                if canonical_role in mapping:
                    break

        # Fallback heuristic: generic 'amount' if specific amount not mapped
        if "amount" not in mapping:
            for col in columns:
                if any(k in str(col).lower() for k in ["amount", "expenditure", "cost", "fund"]):
                    mapping["amount"] = col
                    break

        # Fallback heuristic: generic 'date' if specific date not mapped
        date_candidates = [k for k in mapping if "date" in k]
        if not date_candidates:
            for col in columns:
                if any(k in str(col).lower() for k in ["date", "day", "time"]):
                    mapping["date"] = col
                    break

        return mapping

    def get_canonical_series(self, df: pd.DataFrame, semantic_role: str) -> pd.Series | None:
        """
        Retrieves the series for a given semantic role if present.
        """
        mapping = self.detect_semantic_columns(df)
        col_name = mapping.get(semantic_role)
        if col_name and col_name in df.columns:
            return df[col_name]
        return None

