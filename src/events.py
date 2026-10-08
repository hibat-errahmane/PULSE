import pandas as pd


def build_events(z, gap_days=14):
    """Group active weeks into events. Returns a list of z-score DataFrames."""
    active = (z > 3).any(axis=1) | ((z > 2).sum(axis=1) >= 2)
    act = z[active]
    gap = act.index.to_series().diff().dt.days > gap_days
    return [g for _, g in act.groupby(gap.cumsum())]
