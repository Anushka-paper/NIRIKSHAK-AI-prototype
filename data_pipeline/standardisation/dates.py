import pandas as pd

def standardise_date_column(df, col_name, canonical_col_name):
    if col_name in df.columns:
        # Preserve raw column
        df[f"raw_{col_name}"] = df[col_name].astype(str)
        parsed = pd.to_datetime(df[col_name], format='mixed', errors='coerce')
        df[canonical_col_name] = parsed.dt.strftime('%Y-%m-%d').where(parsed.notna(), None)
    return df
