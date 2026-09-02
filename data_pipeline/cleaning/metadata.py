import pandas as pd

def is_grand_total_row(row):
    row_values_str = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
    return 'grand total' in row_values_str or 'total:' in row_values_str

def is_repeated_header_row(row, columns):
    row_vals = [str(v).strip().lower() for v in row.values]
    col_vals = [str(c).strip().lower() for c in columns]
    matches = sum(1 for r, c in zip(row_vals, col_vals) if r == c)
    return matches >= (len(columns) // 2)
