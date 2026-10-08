import json
from collections import Counter

inv = json.load(open("data/processed/investigation.json"))
ev = {e["id"]: e for e in json.load(open("data/processed/evidence.json"))["events"]}

# Sellers that appear as top offenders in more than one event
seen = Counter()
for r in inv:
    if r["investigated"]:
        for s in r["sellers"]["strongest_abnormal_change"]:
            seen[s["group"]] += 1
repeat = {g for g, c in seen.items() if c >= 2}

RECS = {
    "localized": "Problem is concentrated in one area. Check carriers and logistics for {top} first.",
    "systemic": "Problem is broad across sellers, regions and categories. Look at network-wide capacity (carrier load, seasonal peak) before blaming any seller.",
    "hotspot": "Problem is concentrated but not exclusive. Start with {top}, then review overall capacity.",
    "mixed": "No clear single cause. Keep monitoring.",
}

def build(r):
    out = {"id": r["id"], "start": r["start"], "end": r["end"], "severity": ev[r["id"]]["severity"]}
    if not r["investigated"]:
        out.update(kind="no_late_signal", headline="Anomaly not driven by late deliveries.",
                   recommendation="Review other signals (orders, review scores) for this period.")
        return out
    p = r["pooled_late_rate_pct"]
    reg = r["regions"]
    top = reg["strongest_abnormal_change"][0]
    share = top["excess_share_pct"] or 0
    broad = reg["flagged_groups"] / max(reg["eligible_groups"], 1) >= 0.5
    if share >= 50:
        kind = "localized"
    elif broad:
        kind = "systemic"
    elif share >= 30:
        kind = "hotspot"
    else:
        kind = "mixed"
    rec = RECS[kind].format(top=top["group"])
    if kind == "systemic" and share >= 30:
        rec += f" {top['group']} is the biggest hotspot ({share:.0f}% of excess late orders)."
    out.update(
        kind=kind,
        headline=f"Late deliveries rose from {p['baseline']}% to {p['event']}% ({p['delivered_orders_event']} orders).",
        top_region=top["group"], top_region_share_pct=share,
        repeat_sellers=[s["group"] for s in r["sellers"]["strongest_abnormal_change"] if s["group"] in repeat],
        reliability="low volume, watch only" if p["delivered_orders_event"] < 1500 else "solid sample",
        recommendation=rec)
    return out

report = [build(r) for r in inv]
json.dump(report, open("data/processed/report.json", "w"), indent=2)
for x in report:
    print(f"\nEVENT {x['id']} ({x['start']} to {x['end']}, {x['severity']}): {x['kind']}")
    print("  ", x["headline"])
    if "reliability" in x:
        print("   Reliability:", x["reliability"])
        if x["repeat_sellers"]:
            print("   Repeat sellers:", [s[:8] for s in x["repeat_sellers"]])
    print("   ->", x["recommendation"])