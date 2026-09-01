def find_exact_duplicates(df, composite_keys=['work_id', 'vendor_id', 'amount', 'txn_date']):
    """Identifies exact duplicate transactions by composite key."""
    return df[df.duplicated(subset=composite_keys, keep=False)]

