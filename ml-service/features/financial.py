def compute_financial_features(df):
    """Computes cost estimate variance, overrun %, amount z-scores."""
    df['estimate_variance_pct'] = ((df['sanctioned_amount'] - df['recommended_amount']) / df['recommended_amount']) * 100
    return df

