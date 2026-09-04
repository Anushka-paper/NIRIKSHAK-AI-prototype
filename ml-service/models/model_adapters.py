"""
Stage 5 — MODEL-SPECIFIC ADAPTERS (thin, per model)
- Dedup -> pulls work_description text from Works
- Cost anomaly -> pulls numeric features from feature store as-is
- Trend forecast -> resamples Expenditure into per-MP time series
- Delay prediction -> builds duration/event columns from Sanction/Completion dates
- Vendor graph -> builds edge list from Expenditure (vendor_id <-> district)
- Calamity anomaly -> spike detection on Calamity_Consent alone (standalone stream)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Stage5-ModelAdapters")

class ModelAdapters:
    """
    Thin model-specific adapters preparing feature subsets for downstream ML models.
    """

    @staticmethod
    def get_dedup_dataset(canonical_works: pd.DataFrame) -> pd.DataFrame:
        """Pulls work_description text from Works for Sentence-BERT text dedup."""
        if canonical_works.empty:
            return pd.DataFrame(columns=["work_id", "constituency_id", "work_description"])
        df = canonical_works[["work_id", "constituency_id", "description"]].copy()
        df.rename(columns={"description": "work_description"}, inplace=True)
        return df[df["work_description"].str.strip() != ""]

    @staticmethod
    def get_cost_anomaly_dataset(feature_store: pd.DataFrame) -> pd.DataFrame:
        """Pulls numeric features from feature store for Isolation Forest & Autoencoder."""
        cols = [
            "work_id", "sanction_amount", "district_category_median",
            "cost_deviation_pct", "total_expenditure_vs_sanction_amount",
            "category", "state"
        ]
        available = [c for c in cols if c in feature_store.columns]
        return feature_store[available].dropna(subset=["sanction_amount"])

    @staticmethod
    def get_delay_prediction_dataset(feature_store: pd.DataFrame) -> pd.DataFrame:
        """Builds duration/event columns from Sanction/Completion dates."""
        cols = [
            "work_id", "category", "state", "sanction_amount",
            "recommendation_to_sanction_days", "sanction_to_first_payment_days",
            "total_execution_days", "status"
        ]
        available = [c for c in cols if c in feature_store.columns]
        df = feature_store[available].copy()
        df["is_delayed"] = df["total_execution_days"] > 365
        return df

    @staticmethod
    def get_trend_forecast_dataset(canonical_expenditure: pd.DataFrame) -> pd.DataFrame:
        """Resamples Expenditure into per-MP time series for Prophet/ARIMA."""
        if canonical_expenditure.empty:
            return pd.DataFrame()
        df = canonical_expenditure.copy()
        df["ds"] = pd.to_datetime(df["txn_date"], errors="coerce")
        df = df.dropna(subset=["ds"])
        # Aggregate monthly
        monthly = df.groupby(["state", pd.Grouper(key="ds", freq="M")])["amount"].sum().reset_index()
        monthly.rename(columns={"amount": "y"}, inplace=True)
        return monthly

    @staticmethod
    def get_vendor_graph_edgelist(canonical_expenditure: pd.DataFrame) -> pd.DataFrame:
        """Builds edge list from Expenditure (vendor_id <-> district/state)."""
        if canonical_expenditure.empty or "vendor_id" not in canonical_expenditure.columns:
            return pd.DataFrame()
        edges = canonical_expenditure.groupby(["vendor_id", "state"]).agg(
            total_contracts=("work_id", "nunique"),
            total_disbursed=("amount", "sum")
        ).reset_index()
        return edges

    @staticmethod
    def get_calamity_anomaly_dataset(canonical_calamity: pd.DataFrame) -> pd.DataFrame:
        """Pulls standalone disaster stream for Calamity spike detection."""
        if canonical_calamity.empty:
            return pd.DataFrame()
        df = canonical_calamity.copy()
        df["consent_date"] = pd.to_datetime(df["consent_date"], errors="coerce")
        # Compute frequency and sudden volume spikes
        return df.sort_values(by="consent_date")
