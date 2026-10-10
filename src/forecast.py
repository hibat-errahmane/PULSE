import numpy as np
import pandas as pd

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
sig = sig.iloc[:-1]  # last week is partial, so drop it
H, W, R = 4, 12, 2   # horizon, band window, level window

rows = []
for col in ["orders", "avg_score", "pct_late"]:
    level = sig[col].iloc[-R:].mean()
    s = sig[col].iloc[-W:].std(ddof=1)
    for h in range(1, H + 1):
        lo, hi = level - 1.96 * s, level + 1.96 * s
        if col == "avg_score":
            lo, hi = max(lo, 1.0), min(hi, 5.0)
        else:
            lo = max(lo, 0.0)
        rows.append({"signal": col,
                     "week": sig.index[-1] + pd.DateOffset(weeks=h),
                     "yhat": level, "lo": lo, "hi": hi})

fc = pd.DataFrame(rows)
fc.to_csv("data/processed/forecast.csv", index=False)
print(fc.round(3).to_string(index=False))