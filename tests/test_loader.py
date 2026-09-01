import pytest
import pandas as pd
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from ingestion.data_loader import DataLoader, discover_datasets, load_dataset

def test_data_loader_discovery():
    loader = DataLoader(base_dir=BASE_DIR / "data" / "raw")
    discovered = loader.discover(parliament="all")

    assert "lok_sabha" in discovered
    assert "rajya_sabha" in discovered
    assert len(discovered["lok_sabha"]) > 0

def test_single_dataset_load():
    ds_file = BASE_DIR / "data" / "raw" / "lok_sabha" / "allocation.csv"
    if not ds_file.exists():
        ds_file = BASE_DIR / "data" / "raw" / "allocation.csv"

    result = load_dataset(ds_file, parliament="lok_sabha")

    assert result["metadata"]["load_status"] == "success"
    assert result["metadata"]["rows"] > 0
    assert result["metadata"]["columns"] > 0
    assert isinstance(result["data"], pd.DataFrame)

def test_missing_dataset_graceful_handling():
    result = load_dataset(BASE_DIR / "data" / "raw" / "non_existent_file.csv", parliament="lok_sabha")

    assert result["metadata"]["load_status"] == "failed"
    assert result["data"] is None
