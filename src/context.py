import json
import pandas as pd

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
with open("data/processed/evidence.json") as fh:
    data = json.load(fh)

CHECK = {"avg_score": (1, -0.15), "pct_late": (100, 5.0)}  # (scale, gap that counts as worse)

for ev in data["events"]:
    start = pd.Timestamp(ev["start"])
    ev["context"] = {}
    ev.pop("caveat", None)
    notes = []
    print(f"EVENT {ev['id']} {ev['start']} to {ev['end']}")
    for s, (scale, limit) in CHECK.items():
        hist = float(sig[s].loc[:start].iloc[:-1].median()) * scale
        f = ev["facts"][s]
        gap = f["event_mean"] - hist
        worse = gap <= limit if limit < 0 else gap >= limit
        ev["context"][s] = {"history_median": round(hist, 2), "gap_vs_history": round(gap, 2),
                            "worse_than_history": bool(worse)}
        print(f"  {s}: event {f['event_mean']} | history median {hist:.2f} | gap {gap:+.2f} | peak z {f['peak_z']}")
        if worse and f["peak_z"] <= 2:
            notes.append(f"{s} did not change versus the previous 12 weeks, but is still worse than the "
                         f"longer history (history median {hist:.2f}, event {f['event_mean']}).")
    if notes:
        ev["caveat"] = " ".join(notes)
        print("  CAVEAT:", ev["caveat"])

with open("data/processed/evidence.json", "w") as fh:
    json.dump(data, fh, indent=2)
