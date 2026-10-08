import numpy as np
import pandas as pd
from anomaly_detection import robust_z

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
base = sig["orders"].astype(float)
length, th = 2, 3
starts = range(12, len(base) - length + 1)

rows = []
for w in (8, 12, 20, 26):
    clean = robust_z(np.log(base), window=w).dropna()
    for drop in (0.3, 0.5):
        hits = 0
        for st in starts:
            s = base.copy()
            s.iloc[st:st + length] *= (1 - drop)
            z = robust_z(np.log(s), window=w).iloc[st:st + length]
            hits += bool((z < -th).any())
        rows.append({
            "window": w,
            "drop_pct": int(drop * 100),
            "detected_pct": round(100 * hits / len(starts), 1),
            "clean_down_flags_per_100wk": round(100 * float((clean < -th).mean()), 1),
        })
print("events tested per setting:", len(starts))
print(pd.DataFrame(rows).to_string(index=False))
