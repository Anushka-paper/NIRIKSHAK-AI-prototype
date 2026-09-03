from .financial import compute_financial_features
from .temporal import compute_temporal_features
from .payment import compute_payment_features

def build_feature_store(df):
    """Master Orchestrator for Canonical Feature Store Generation."""
    df = compute_financial_features(df)
    df = compute_temporal_features(df)
    df = compute_payment_features(df)
    return df

