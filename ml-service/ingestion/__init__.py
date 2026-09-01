"""
NIRIKSHAK AI Ingestion Package
"""
from .data_loader import (
    DataLoader,
    discover_datasets,
    load_dataset,
    load_parliament_datasets,
    load_all_datasets
)

__all__ = [
    "DataLoader",
    "discover_datasets",
    "load_dataset",
    "load_parliament_datasets",
    "load_all_datasets"
]
