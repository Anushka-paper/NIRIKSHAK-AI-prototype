import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from data_pipeline.ml_anomaly.config import ML_FEATURE_COLS

def prepare_feature_matrix(df_work, df_txn=None, df_vendor=None):
    if df_work.empty:
        return np.array([]), df_work, ML_FEATURE_COLS
        
    df = df_work.copy()
    
    # Merge transaction & vendor features if provided
    if df_txn is not None and not df_txn.empty and "canonical_work_id" in df_txn.columns:
        txn_agg = df_txn.groupby("canonical_work_id")["amount_zscore"].max().reset_index()
        df = df.merge(txn_agg, on="canonical_work_id", how="left")
        
    if df_vendor is not None and not df_vendor.empty and "canonical_mp_name" in df_work.columns:
        v_agg = df_vendor.groupby("canonical_name")["concentration_pct"].max().reset_index()
        df = df.merge(v_agg, left_on="canonical_mp_name", right_on="canonical_name", how="left")

    for col in ML_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            
    raw_X = df[ML_FEATURE_COLS].values
    
    imputer = SimpleImputer(strategy="median")
    scaler = RobustScaler()
    
    X_imp = imputer.fit_transform(raw_X)
    X_scaled = scaler.fit_transform(X_imp)
    
    return X_scaled, df, ML_FEATURE_COLS
