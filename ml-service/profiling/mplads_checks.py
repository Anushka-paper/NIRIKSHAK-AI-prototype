import pandas as pd
from .amount_checks import parse_currency_to_float

MPLADS_HEADER_KEYWORDS = [
    'state', 'mp', 'parliament', 'constituency', 'work', 'ida',
    'sanction', 'allocation', 'recommended', 'expenditure', 'calamity'
]

def is_mplads_dataset(df: pd.DataFrame) -> bool:
    """Checks if dataset headers match MPLADS domain keywords."""
    cols_clean = [col.lower().strip() for col in df.columns]
    matches = sum(1 for c in cols_clean if any(k in c for k in MPLADS_HEADER_KEYWORDS))
    return matches >= 2

def run_mplads_profiling(df: pd.DataFrame) -> dict:
    """Runs domain-aware MPLADS geographical and monetary breakdowns."""
    if not is_mplads_dataset(df):
        return {"is_mplads_domain": False}

    mplads_report = {"is_mplads_domain": True}

    state_col = next((c for c in df.columns if 'state' in c.lower()), None)
    const_col = next((c for c in df.columns if 'constituency' in c.lower()), None)
    amount_col = next((c for c in df.columns if any(k in c.lower() for k in ['amount', 'allocated', 'sanction', 'expenditure'])), None)

    if state_col and amount_col:
        df_copy = df[[state_col, amount_col]].copy()
        if const_col and const_col in df.columns:
            df_copy[const_col] = df[const_col]

        df_copy['numeric_amount'] = df_copy[amount_col].apply(parse_currency_to_float)

        state_groups = df_copy.groupby(state_col)
        state_summary = {}
        total_data_amount = df_copy['numeric_amount'].sum()

        for state_name, group in state_groups:
            state_tot = float(group['numeric_amount'].sum())
            state_summary[state_name] = {
                "record_count": int(len(group)),
                "total_amount": round(state_tot, 2),
                "average_amount": round(float(group['numeric_amount'].mean()), 2) if len(group) > 0 else 0.0,
                "percentage_share": round((state_tot / (total_data_amount or 1)) * 100, 2),
                "constituencies_count": int(group[const_col].nunique()) if const_col and const_col in group else 0
            }

        mplads_report["geographical_breakdown"] = {
            "state_column_used": state_col,
            "amount_column_used": amount_col,
            "total_dataset_amount": round(float(total_data_amount), 2),
            "state_summaries": state_summary
        }

    return mplads_report
