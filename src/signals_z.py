import numpy as np
import pandas as pd
from anomaly_detection import robust_z

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
z = pd.DataFrame({
    "orders": -robust_z(np.log(sig["orders"].astype(float))),
    "avg_score": -robust_z(sig["avg_score"], scale_floor=0.05),
    "pct_late": robust_z(sig["pct_late"], scale_floor=0.01),
}).dropna()
z.to_csv("data/processed/weekly_z.csv")

print("weeks:", len(z))
print("weeks with z > 3, per signal:")
print((z > 3).sum().to_string())
print()
multi = z[(z > 2).sum(axis=1) >= 2]
print("weeks where at least 2 signals have z > 2:", len(multi))
print(multi.round(1).to_string())
