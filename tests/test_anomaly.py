import numpy as np
import pandas as pd

from src.anomaly_detection import robust_z


def test_no_future_leakage():
    s = pd.Series(np.random.default_rng(0).normal(100, 5, 40))
    s2 = s.copy()
    s2.iloc[25] = 1000.0
    assert robust_z(s).iloc[:25].equals(robust_z(s2).iloc[:25])


def test_spike_is_flagged():
    s = pd.Series(np.random.default_rng(0).normal(100, 5, 40))
    s.iloc[30] = 300.0
    assert robust_z(s).iloc[30] > 3
