import sys
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
import numpy as np
import pandas as pd

P = "data/raw/olist/"
MIN_SHOW, MIN_ELIGIBLE, MIN_SCORE_N, Z = 10, 20, 10, 1.96


def load_fact():
    """One row per order, plus seller_id for single-seller orders only."""
    f = pd.read_csv("data/processed/orders_fact.csv",
                    parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                 "order_estimated_delivery_date", "review_creation_date"])
    items = pd.read_csv(P + "olist_order_items_dataset.csv",
                        usecols=["order_id", "seller_id"]).drop_duplicates()
    n_sellers = items.groupby("order_id")["seller_id"].transform("nunique")
    f = f.merge(items[n_sellers == 1], on="order_id", how="left", validate="one_to_one")
    return f

def wilson_lo(k, n, z=Z):
    """Lower end of the 95% Wilson interval for a rate k/n."""
    p = k / n
    centre = p + z**2 / (2 * n)
    adj = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (centre - adj) / (1 + z**2 / n)


def windows(start, end, base_weeks=12):
    """Week labels are week-END dates, so the event starts 6 days before `start`.
    Baseline = the 12 weeks before the event (same as evidence.py). Half-open [a, b)."""
    ev0 = pd.Timestamp(start) - pd.Timedelta(days=6)
    ev1 = pd.Timestamp(end) + pd.Timedelta(days=1)
    return (ev0, ev1), (ev0 - pd.Timedelta(weeks=base_weeks), ev0)


def late_stats(f, key, win):
    d = f[(f["order_delivered_customer_date"] >= win[0]) & (f["order_delivered_customer_date"] < win[1])]
    return d.dropna(subset=["late", key]).groupby(key)["late"].agg(n="size", late="sum")


def score_stats(f, key, win):
    d = f[(f["review_creation_date"] >= win[0]) & (f["review_creation_date"] < win[1])]
    return d.dropna(subset=["review_score", key]).groupby(key)["review_score"].agg(n_rev="size", score="mean")


def drill(f, key, start, end):
    ev, ba = windows(start, end)
    e, b = late_stats(f, key, ev), late_stats(f, key, ba)
    t = e.rename(columns={"n": "n_event", "late": "late_event"}).join(
        b.rename(columns={"n": "n_base", "late": "late_base"}), how="left")
    t[["n_base", "late_base"]] = t[["n_base", "late_base"]].fillna(0)
    t = t.join(score_stats(f, key, ev).rename(columns={"n_rev": "nrev_event", "score": "score_event"}))
    t = t.join(score_stats(f, key, ba).rename(columns={"n_rev": "nrev_base", "score": "score_base"}))
    for c in ("nrev_event", "nrev_base"):
        t[c] = t[c].fillna(0)
    t.loc[t["nrev_event"] < MIN_SCORE_N, "score_event"] = np.nan
    t.loc[t["nrev_base"] < MIN_SCORE_N, "score_base"] = np.nan

    t["rate_event"] = t["late_event"] / t["n_event"]
    t["rate_base"] = t["late_base"] / t["n_base"].replace(0, np.nan)
    t["change_pp"] = (t["rate_event"] - t["rate_base"]) * 100
    t["lo_event"] = wilson_lo(t["late_event"], t["n_event"])

    # CONTRIBUTION: share of all late deliveries in the event window
    tot_late, tot_n = t["late_event"].sum(), t["n_event"].sum()
    t["contribution_pct"] = 100 * t["late_event"] / tot_late
    # EXCESS: late orders beyond what the group's own baseline rate predicts
    base_rate_all = b["late"].sum() / b["n"].sum()
    # groups with no baseline use the pooled baseline rate
    t["excess_late"] = t["late_event"] - t["n_event"] * t["rate_base"].fillna(base_rate_all)
    excess_total = t["excess_late"].clip(lower=0).sum()
    t["excess_share_pct"] = 100 * t["excess_late"].clip(lower=0) / excess_total
    t["excess_share_pct"] = 100 * t["excess_late"].clip(lower=0) / excess_total

    def status(r):
        if r["n_event"] < MIN_SHOW:
            return "insufficient"
        if r["n_event"] < MIN_ELIGIBLE:
            return "low sample"
        if r["n_base"] < MIN_ELIGIBLE:
            return "no baseline"
        return "ABNORMAL" if r["lo_event"] > r["rate_base"] else "normal range"
    t["status"] = t.apply(status, axis=1)
    totals = {"n_event": tot_n, "rate_event": tot_late / tot_n, "rate_base": base_rate_all,
              "excess_total": excess_total, "windows": (ev, ba)}
    return t, totals


def show(t, totals, key):
    ev, ba = totals["windows"]
    print(f"Group: {key}")
    print(f"Event window   : {ev[0].date()} to {(ev[1] - pd.Timedelta(days=1)).date()}")
    print(f"Baseline window: {ba[0].date()} to {(ba[1] - pd.Timedelta(days=1)).date()}")
    print(f"Delivered orders in event (with a {key}): {totals['n_event']}")
    print(f"Pooled late rate: baseline {100*totals['rate_base']:.2f}% -> event {100*totals['rate_event']:.2f}%")
    elig = t[(t["n_event"] >= MIN_ELIGIBLE) & (t["n_base"] >= MIN_ELIGIBLE)]
    print(f"Eligible groups (n>={MIN_ELIGIBLE} in both windows): {len(elig)} "
          f"covering {100*elig['n_event'].sum()/totals['n_event']:.0f}% of event orders")
    print("Status counts:", t["status"].value_counts().to_dict())

    cols = ["n_event", "rate_base", "rate_event", "change_pp", "contribution_pct", "excess_late", "excess_share_pct", "status"]

    def fmt(d):
        d = d[cols].copy()
        d.index = [str(i)[:24] for i in d.index]
        d["rate_base"] *= 100
        d["rate_event"] *= 100
        return d.round(1).to_string()

    ab = t[t["status"] == "ABNORMAL"].sort_values("excess_late", ascending=False)
    print(f"\nStrongest abnormal change (sorted by excess late orders), top 10 of {len(ab)}:")
    print(fmt(ab.head(10)) if len(ab) else "  none")
    print("\nLargest contribution to event late deliveries, top 10 (any status):")
    print(fmt(t.sort_values("contribution_pct", ascending=False).head(10)))
    print(f"\nNote: with {len(elig)} eligible groups and a one-sided 95% test, about "
          f"{0.025*len(elig):.1f} could be flagged by chance alone.")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "seller_id"
    fact = load_fact()
    table, totals = drill(fact, key, "2017-12-17", "2018-01-14")
    show(table, totals, key)
