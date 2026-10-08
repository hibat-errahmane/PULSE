import json
import pandas as pd
from events import build_events

FAMILY = {"orders": "demand", "avg_score": "fulfillment", "pct_late": "fulfillment"}
UNIT = {"orders": "relative", "avg_score": "points", "pct_late": "percentage points"}
LEVELS = ["LOW", "MEDIUM", "HIGH"]
LATE_REC = "Check the late-delivery rate by seller and by customer region for these weeks (not computed yet)."
TEXT = {
    "demand": ("Orders fell while delivery and review signals stayed normal; these signals do not explain the drop.",
               "Check whether the drop is across all product categories or only some, and look for external disruptions in these weeks."),
    "fulfil_both": ("Late deliveries rose and review scores fell together while orders did not drop; delivery problems may be hurting customer satisfaction.", LATE_REC),
    "late": ("Late deliveries rose without a clear review-score drop.", LATE_REC),
    "score": ("Review scores fell without a clear rise in late deliveries; the cause is not visible in these signals.",
              "Compare scores by product category and read the lowest-scored reviews of these weeks."),
    "mixed": ("Orders and delivery/review signals changed in the same period; they may or may not be related.",
              "Investigate the demand drop and the fulfillment signals separately first."),
}

sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
z = pd.read_csv("data/processed/weekly_z.csv", index_col=0, parse_dates=True)


def severity(peak, weeks):
    return LEVELS[int(peak >= 5) + int(weeks >= 3)]


def confidence(flagged, weeks):
    fams = {FAMILY[s] for s in flagged}
    level = 2 if len(fams) >= 2 else (1 if len(flagged) >= 2 else 0)
    if weeks == 1:
        level = max(level - 1, 0)
    return LEVELS[level]


def pick(flagged):
    f = set(flagged)
    if "orders" in f and len(f) > 1:
        return "mixed"
    if f == {"orders"}:
        return "demand"
    if f == {"avg_score", "pct_late"}:
        return "fulfil_both"
    return "late" if f == {"pct_late"} else "score"


records = []
for i, g in enumerate(build_events(z), 1):
    start, end = g.index[0], g.index[-1]
    weeks = (end - start).days // 7 + 1
    peaks = g.max()
    flagged = [s for s in z.columns if peaks[s] > 2]
    sev, conf = severity(float(peaks.max()), weeks), confidence(flagged, weeks)
    facts = {}
    for s in z.columns:
        scale = 100 if s == "pct_late" else 1
        base = float(sig[s].loc[:start].iloc[:-1].iloc[-12:].median()) * scale
        cur = float(sig[s].loc[start:end].mean()) * scale
        change = cur / base - 1 if s == "orders" else cur - base
        facts[s] = {"baseline": round(base, 2), "event_mean": round(cur, 2),
                    "change": round(change, 3), "unit": UNIT[s], "peak_z": round(float(peaks[s]), 1)}
    hyp, rec = TEXT[pick(flagged)]
    records.append({"id": i, "start": str(start.date()), "end": str(end.date()), "weeks": weeks,
                    "severity": sev, "confidence": conf, "flagged": flagged,
                    "facts": facts, "hypothesis": hyp, "recommendation": rec})
    print(f"EVENT {i}: {start.date()} to {end.date()} ({weeks} weeks)")
    print(f"Severity: {sev} | Confidence: {conf}")
    print("Observed:")
    for s, f in facts.items():
        print(f"  {s}: baseline {f['baseline']}, event {f['event_mean']}, change {f['change']} ({f['unit']}), peak z {f['peak_z']}")
    print("Hypothesis (not established, timing association only):", hyp)
    print("Suggested investigation:", rec)
    print()

with open("data/processed/evidence.json", "w") as fh:
    json.dump({"events": records}, fh, indent=2)
print("severity:", pd.Series([r["severity"] for r in records]).value_counts().to_dict())
print("confidence:", pd.Series([r["confidence"] for r in records]).value_counts().to_dict())
