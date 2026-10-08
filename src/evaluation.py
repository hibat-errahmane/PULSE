import numpy as np
import pandas as pd
from anomaly_detection import robust_z

TRANSFORMS = {"level": lambda x: x, "log": np.log}


def evaluate(drop, transform, length=2, thresholds=(3, 4, 5), n=30, seed=0):
    sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
    base = sig["orders"].astype(float)
    tf = TRANSFORMS[transform]
    rng = np.random.default_rng(seed)
    starts = rng.integers(12, len(base) - length, size=n)
    clean_z = robust_z(tf(base)).dropna()
    rows = []
    for th in thresholds:
        hits, delays = 0, []
        for st in starts:
            s = base.copy()
            s.iloc[st:st + length] *= (1 - drop)
            w = robust_z(tf(s)).iloc[st:st + length]
            flagged = (w < -th).to_numpy()
            if flagged.any():
                hits += 1
                delays.append(int(np.argmax(flagged)))
        rows.append({
            "transform": transform,
            "threshold": th,
            "detected_pct": round(100 * hits / n, 1),
            "mean_delay_weeks": round(float(np.mean(delays)), 2) if delays else None,
            "clean_down_flags_per_100wk": round(100 * float((clean_z < -th).mean()), 1),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    for d in (0.3, 0.5):
        print("injected drop:", int(d * 100), "% for 2 weeks")
        print(pd.concat([evaluate(d, t) for t in TRANSFORMS]).to_string(index=False))
        print()
