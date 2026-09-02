import pandas as pd

def validate_currency_rules(df):
    amount_cols = [c for c in df.columns if "amount" in c or "limit" in c or "disbursed" in c]
    negatives = {}
    large_amounts = {}
    
    for col in amount_cols:
        numeric_s = pd.to_numeric(df[col], errors='coerce')
        neg_count = int((numeric_s < 0).sum())
        large_count = int((numeric_s > 1000000000).sum())
        
        if neg_count > 0:
            negatives[col] = neg_count
        if large_count > 0:
            large_amounts[col] = large_count
            
    return negatives, large_amounts
