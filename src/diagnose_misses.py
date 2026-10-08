import numpy as np
import pandas as pd
from anomaly_detection import robust_z

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
base = sig["orders"].astype(float)
length = 2
rng = np.random.default_rng(0)
starts = rng.integers(12, len(base) - length, size=30)

rows = []
for st in sorted(starts):
    s = base.copy()
    s.iloc[st:st + length] *= 0.5
    w = robust_z(np.log(s)).iloc[st:st + length]
    rows.append({
        "start": base.index[st].date(),
        "min_z": round(float(w.min()), 1),
        "detected": bool((w < -3).any()),
    })
print(pd.DataFrame(rows).to_string(index=False))
