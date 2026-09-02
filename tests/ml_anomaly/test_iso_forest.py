import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import numpy as np
from data_pipeline.ml_anomaly.iso_forest import train_isolation_forest

def test_train_isolation_forest():
    X = np.random.randn(20, 5)
    scores, clf = train_isolation_forest(X, save_model=False)
    assert len(scores) == 20
    assert clf is not None
