import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import numpy as np
from data_pipeline.predictive.delay_model import train_delay_models

def test_train_delay_models():
    X_tr = np.random.randn(30, 5)
    y_clf = np.random.randint(0, 2, size=30)
    y_reg = np.random.uniform(0, 100, size=30)
    
    probs, days, clf, reg, metrics = train_delay_models(X_tr, y_clf, y_reg, X_tr)
    assert len(probs) == 30
    assert len(days) == 30
    assert "delay_roc_auc" in metrics
