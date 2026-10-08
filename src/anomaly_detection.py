import pandas as pd


def robust_z(s, window=12, min_periods=8, scale_floor=0.0):
    """Robust z-score vs median/MAD of the PREVIOUS weeks only (no leakage)."""
    past = s.shift(1)
    med = past.rolling(window, min_periods=min_periods).median()
    mad = past.rolling(window, min_periods=min_periods).apply(
        lambda x: (x - x.median()).abs().median(), raw=False)
    scale = (1.4826 * mad).clip(lower=scale_floor)
    return (s - med) / scale
