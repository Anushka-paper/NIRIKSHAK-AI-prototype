import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from data_pipeline.ml_anomaly.config import ML_FEATURE_COLS

def prepare_feature_matrix(df_work, df_txn=None, df_vendor=None):
    """
    Robust Preprocessing Pipeline with missingness preservation and heavy-tail scaling (§8).
    """
    if df_work is None or df_work.empty:
        return np.array([]), pd.DataFrame(), ML_FEATURE_COLS

    df = df_work.copy()

    # Merge transaction & vendor features if provided
    if df_txn is not None and not df_txn.empty and "canonical_work_id" in df_txn.columns:
        if "amount_zscore" in df_txn.columns:
            txn_agg = df_txn.groupby("canonical_work_id")["amount_zscore"].max().reset_index()
            df = df.merge(txn_agg, on="canonical_work_id", how="left")

    if df_vendor is not None and not df_vendor.empty and "canonical_mp_name" in df_work.columns:
        if "vendor_concentration_pct" in df_vendor.columns:
            v_agg = df_vendor.groupby("canonical_vendor_name")["vendor_concentration_pct"].max().reset_index()
            df = df.merge(v_agg, left_on="canonical_mp_name", right_on="canonical_vendor_name", how="left")

    expanded_feature_cols = list(ML_FEATURE_COLS)
    
    # 1. Missingness Preservation: add was_missing indicator for every feature (§8, Question 5)
    for col in ML_FEATURE_COLS:
        if col not in df.columns:
            df[col] = np.nan
            
        # Create boolean missing indicator column
        missing_col_name = f"{col}_was_missing"
        df[missing_col_name] = df[col].isna().astype(float)
        expanded_feature_cols.append(missing_col_name)

        # Convert numeric and safely fill NaN with 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 2. Categorical Frequency Encoding (§8, Question 4)
    cat_cols = [c for c in ["canonical_state", "canonical_work_category"] if c in df.columns]
    for c in cat_cols:
        freq = df[c].value_counts(normalize=True).to_dict()
        freq_col_name = f"{c}_freq_encoded"
        df[freq_col_name] = df[c].map(freq).fillna(0.0)
        expanded_feature_cols.append(freq_col_name)

    raw_X = df[expanded_feature_cols].values

    # 3. SimpleImputer for numeric values + RobustScaler for heavy-tailed financial distributions (§8, Question 6)
    imputer = SimpleImputer(strategy="median", fill_value=0.0)
    scaler = RobustScaler(with_centering=True, with_scaling=True)

    X_imp = imputer.fit_transform(raw_X)
    X_scaled = scaler.fit_transform(X_imp)

    print(f"[ML PREPROCESSOR] Transformed {len(df):,} records into {X_scaled.shape[1]}-dimensional RobustScaled feature matrix.")
    return X_scaled, df, expanded_feature_cols
