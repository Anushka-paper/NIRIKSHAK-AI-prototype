import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml-service"))

from pipeline import NirikshakPipeline

def test_pipeline_execution_lok_sabha(tmp_path):
    prof_dir = tmp_path / "profiling"
    std_dir = tmp_path / "standardized"

    pipeline = NirikshakPipeline(
        raw_dir=BASE_DIR / "data" / "raw",
        profiling_dir=prof_dir,
        standardized_dir=std_dir
    )

    summary = pipeline.run(parliament="lok_sabha")

    assert "lok_sabha" in summary["parliaments_processed"]
    assert summary["parliaments_processed"]["lok_sabha"]["datasets_discovered"] > 0
    assert summary["parliaments_processed"]["lok_sabha"]["profiling_status"] == "success"
    assert summary["parliaments_processed"]["lok_sabha"]["standardization_status"] == "success"
