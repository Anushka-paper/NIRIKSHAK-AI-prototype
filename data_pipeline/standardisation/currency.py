import pandas as pd

def standardise_currency_column(df, col_name, canonical_col_name):
    if col_name in df.columns:
        # Preserve raw column
        df[f"raw_{col_name}"] = df[col_name].astype(str)
        num_s = pd.to_numeric(df[col_name], errors='coerce')
        df[canonical_col_name] = num_s.where(num_s.notna(), None)
    return df
