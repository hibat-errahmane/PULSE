import numpy as np
import pandas as pd
from anomaly_detection import robust_z

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
O = sig["orders"].astype(float)
S = sig["avg_score"].astype(float)
L = sig["pct_late"].astype(float)
N = len(sig)


def scale_of(s, floor, window=12, min_periods=8):
    past = s.shift(1)
    mad = past.rolling(window, min_periods=min_periods).apply(
        lambda x: (x - x.median()).abs().median(), raw=False)
    return (1.4826 * mad).clip(lower=floor)


def zscores(o, s, l):
    return pd.DataFrame({
        "orders": -robust_z(np.log(o)),
        "avg_score": -robust_z(s, scale_floor=0.05),
        "pct_late": robust_z(l, scale_floor=0.01),
    })


def alerts(z, cols):
    sub = z[cols]
    return (sub > 3).any(axis=1) | ((sub > 2).sum(axis=1) >= 2)


SC_S, SC_L = scale_of(S, 0.05), scale_of(L, 0.01)
EXPS = {
    "A_orders": ["orders"],
    "B_orders+late": ["orders", "pct_late"],
    "C_orders+score": ["orders", "avg_score"],
    "D_all": ["orders", "avg_score", "pct_late"],
}
KINDS = {"demand_30": (0.7, 0.0), "fulfil_weak": (1.0, 2.5), "fulfil_strong": (1.0, 4.0)}
starts = list(range(12, N - 1))

clean_z = zscores(O, S, L)
valid = {}
for e, cols in EXPS.items():
    ca = alerts(clean_z, cols)
    valid[e] = {st for st in starts if not ca.iloc[st:st + 2].any()}

hits = {k: {e: 0 for e in EXPS} for k in KINDS}
for kind, (f, k) in KINDS.items():
    for st in starts:
        o, s, l = O.copy(), S.copy(), L.copy()
        w = slice(st, st + 2)
        o.iloc[w] *= f
        l.iloc[w] += k * SC_L.iloc[w].to_numpy()
        s.iloc[w] -= k * SC_S.iloc[w].to_numpy()
        z = zscores(o, s, l)
        for e, cols in EXPS.items():
            if st in valid[e]:
                hits[kind][e] += bool(alerts(z, cols).iloc[w].any())

res = pd.DataFrame({kind: {e: round(100 * hits[kind][e] / len(valid[e]), 1) for e in EXPS} for kind in KINDS})
res.insert(0, "valid_starts", pd.Series({e: len(valid[e]) for e in EXPS}))
print(res.to_string())

import json, os
os.makedirs("results", exist_ok=True)
res.to_csv("results/experiments_fair.csv")
params = {
    "dataset": "Olist weekly signals 2017-03 to 2018-08",
    "baseline_window_weeks": 12, "min_periods": 8, "orders_transform": "log",
    "scale_floors": {"avg_score": 0.05, "pct_late": 0.01},
    "alert_rule": "any z>3 or at least two z>2",
    "injection": {"demand_30": "orders x0.7 for 2 weeks",
                  "fulfil_weak": "score and late worsen 2.5 local noise units for 2 weeks",
                  "fulfil_strong": "same at 4 noise units"},
    "scoring": "only start weeks with no real alert in the window (per experiment)",
}
with open("results/experiments_fair_params.json", "w") as fh:
    json.dump(params, fh, indent=2)
