import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from data_pipeline.predictive.config import PREDICTIVE_FEATURE_COLS

def prepare_predictive_features(df_work):
    df = df_work.copy()
    
    for col in PREDICTIVE_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            
    raw_X = df[PREDICTIVE_FEATURE_COLS].values
    
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    
    X_imp = imputer.fit_transform(raw_X)
    X_scaled = scaler.fit_transform(X_imp)
    
    return X_scaled, df, PREDICTIVE_FEATURE_COLS
