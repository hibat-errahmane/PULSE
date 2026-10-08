import numpy as np
import pandas as pd

P = "data/raw/olist/"
f = pd.read_csv("data/processed/orders_fact.csv",
                parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
items = pd.read_csv(P + "olist_order_items_dataset.csv", usecols=["order_id", "seller_id"]).drop_duplicates()

# how many sellers does each order have?
ns = items.groupby("order_id")["seller_id"].nunique()
print("orders with 1 seller:", f"{(ns == 1).mean():.1%}", "| 2+ sellers:", int((ns > 1).sum()))
single = items[items["order_id"].isin(ns[ns == 1].index)]
f = f.merge(single, on="order_id", how="left", validate="one_to_one")

# headline event (late rate uses the delivery date axis)
ev = f[(f["order_delivered_customer_date"] >= "2017-12-11") & (f["order_delivered_customer_date"] < "2018-01-15")]
base = f[(f["order_delivered_customer_date"] >= "2017-09-18") & (f["order_delivered_customer_date"] < "2017-12-11")]

def dist(d, key, label):
    n = d.groupby(key).size()
    print(f"\n{label}: {len(n)} groups, {n.sum()} delivered orders")
    print("  quantiles of n:", n.quantile([.25, .5, .75, .9]).round(0).astype(int).to_dict())
    for t in (5, 10, 20, 30, 50):
        keep = n[n >= t]
        print(f"  n>={t:<3} groups: {len(keep):4d} ({len(keep)/len(n):.0%}) | orders covered: {keep.sum()/n.sum():.0%}")

for name, d in (("EVENT", ev), ("BASELINE", base)):
    print(f"\n===== {name} =====")
    dist(d.dropna(subset=["seller_id"]), "seller_id", "sellers")
    dist(d, "customer_state", "states")

print("\n===== noise of a late rate at true rate 10% =====")
for n in (5, 10, 20, 30, 50, 100):
    print(f"n={n:<4} 95% half-width: +/-{196*np.sqrt(.1*.9/n):.1f} percentage points")