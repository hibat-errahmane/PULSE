import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
import json
import numpy as np
import pandas as pd
from drilldown import P, load_fact, drill, MIN_ELIGIBLE


def add_category(f):
    items = pd.read_csv(P + "olist_order_items_dataset.csv", usecols=["order_id", "product_id"])
    prod = pd.read_csv(P + "olist_products_dataset.csv", usecols=["product_id", "product_category_name"])
    tr = pd.read_csv(P + "product_category_name_translation.csv")
    m = items.merge(prod, on="product_id", how="left", validate="many_to_one")
    m = m.merge(tr, on="product_category_name", how="left", validate="many_to_one")
    m["category"] = m["product_category_name_english"].fillna(m["product_category_name"]).fillna("unknown")
    cats = m[["order_id", "category"]].drop_duplicates()
    nc = cats.groupby("order_id")["category"].transform("nunique")
    single = cats[(nc == 1) & (cats["category"] != "unknown")]
    return f.merge(single, on="order_id", how="left", validate="one_to_one")


def rows(t, order_by, only_abnormal, n=3):
    d = t[t["status"] == "ABNORMAL"] if only_abnormal else t
    d = d.sort_values(order_by, ascending=False).head(n)
    return [{"group": str(g), "n_event": int(r["n_event"]),
             "late_base_pct": round(100 * r["rate_base"], 1) if pd.notna(r["rate_base"]) else None,
             "late_event_pct": round(100 * r["rate_event"], 1),
             "change_pp": round(r["change_pp"], 1) if pd.notna(r["change_pp"]) else None,
             "contribution_pct": round(r["contribution_pct"], 1),
             "excess_share_pct": round(r["excess_share_pct"], 1) if pd.notna(r["excess_share_pct"]) else None,
             "status": r["status"]} for g, r in d.iterrows()]


def investigate(f, key, start, end):
    t, tot = drill(f, key, start, end)
    el = t[(t["n_event"] >= MIN_ELIGIBLE) & (t["n_base"] >= MIN_ELIGIBLE)]
    return {"eligible_groups": int(len(el)),
            "coverage_pct": round(100 * el["n_event"].sum() / tot["n_event"]),
            "flagged_groups": int((t["status"] == "ABNORMAL").sum()),
            "strongest_abnormal_change": rows(t, "excess_late", True),
            "highest_contribution": rows(t, "contribution_pct", False)}, tot


if __name__ == "__main__":
    f = add_category(load_fact())
    events = json.load(open("data/processed/evidence.json"))["events"]
    out = []
    for ev in events:
        rec = {"id": ev["id"], "start": ev["start"], "end": ev["end"]}
        if "pct_late" not in ev["flagged"]:
            rec["investigated"] = False
            rec["reason"] = "Late-delivery signal was not flagged in this event, so the late-delivery drill-down does not apply."
        else:
            rec["investigated"] = True
            for name, key in (("sellers", "seller_id"), ("regions", "customer_state"), ("categories", "category")):
                rec[name], tot = investigate(f, key, ev["start"], ev["end"])
            rec["pooled_late_rate_pct"] = {"baseline": round(100 * tot["rate_base"], 2),
                                           "event": round(100 * tot["rate_event"], 2),
                                           "delivered_orders_event": int(tot["n_event"])}
        out.append(rec)

        print(f"\nEVENT {ev['id']}: {ev['start']} to {ev['end']} ({ev['severity']})")
        if not rec["investigated"]:
            print("  ", rec["reason"])
            continue
        p = rec["pooled_late_rate_pct"]
        print(f"  Late rate (pooled): {p['baseline']}% -> {p['event']}% on {p['delivered_orders_event']} delivered orders")
        for name in ("sellers", "regions", "categories"):
            s = rec[name]
            print(f"  {name}: {s['flagged_groups']} flagged of {s['eligible_groups']} eligible (cover {s['coverage_pct']}% of orders)")
            for r in s["strongest_abnormal_change"]:
                print(f"     strongest abnormal change: {r['group'][:24]:24} {r['late_base_pct']}% -> {r['late_event_pct']}% "
                      f"(n={r['n_event']}, {r['excess_share_pct']}% of excess late)")
            if not s["strongest_abnormal_change"]:
                print("     no group passed the sample-size and significance rules")

    with open("data/processed/investigation.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nSaved data/processed/investigation.json")