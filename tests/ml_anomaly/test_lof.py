import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import numpy as np
from data_pipeline.ml_anomaly.lof import train_local_outlier_factor

def test_train_local_outlier_factor():
    X = np.random.randn(20, 5)
    scores, lof = train_local_outlier_factor(X)
    assert len(scores) == 20
    assert lof is not None
