import re
import pandas as pd

def validate_standardized_dataframe(df: pd.DataFrame) -> dict:
    """
    Executes post-standardisation validation checks on DataFrame.
    """
    errors = []
    warnings = []

    for col in df.columns:
        # 1. Validate Date Columns
        if 'date' in col.lower():
            non_null_dates = df[col].dropna().astype(str)
            invalid_dates = [d for d in non_null_dates if not re.match(r'^\d{4}-\d{2}-\d{2}$', d)]
            if invalid_dates:
                warnings.append(f"Column '{col}' has {len(invalid_dates)} non-ISO date values (e.g. {invalid_dates[0]})")

        # 2. Validate Amount Columns
        if any(k in col.lower() for k in ['amount', 'expenditure']):
            non_null_amt = df[col].dropna()
            non_numeric = [v for v in non_null_amt if not isinstance(v, (int, float, float))]
            if non_numeric:
                errors.append(f"Column '{col}' contains non-numeric monetary values")

            negatives = [v for v in non_null_amt if isinstance(v, (int, float)) and v < 0]
            if negatives:
                warnings.append(f"Column '{col}' contains {len(negatives)} negative amount values")

        # 3. Validate Identifier Columns
        if col in ['work_id', 'sr_no']:
            non_null_ids = df[col].dropna()
            non_str = [v for v in non_null_ids if not isinstance(v, str)]
            if non_str:
                errors.append(f"Column '{col}' contains non-string identifier values")

    return {
        "is_valid": len(errors) == 0,
        "validation_errors": errors,
        "validation_warnings": warnings
    }
