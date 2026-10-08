import os
import numpy as np
import pandas as pd

P = "data/raw/olist/"
DATES = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]

o = pd.read_csv(P + "olist_orders_dataset.csv", parse_dates=DATES)
c = pd.read_csv(P + "olist_customers_dataset.csv", usecols=["customer_id", "customer_state"])
r = pd.read_csv(P + "olist_order_reviews_dataset.csv",
                usecols=["order_id", "review_score", "review_creation_date", "review_answer_timestamp"],
                parse_dates=["review_creation_date", "review_answer_timestamp"])

# 1 review per order: keep the most recent one
multi = int((r.groupby("order_id").size() > 1).sum())
r1 = (r.sort_values(["order_id", "review_creation_date", "review_answer_timestamp"])
        .drop_duplicates("order_id", keep="last")
        [["order_id", "review_score", "review_creation_date"]])

# validate= makes pandas raise an error if a join would duplicate rows
df = o.merge(c, on="customer_id", how="left", validate="many_to_one")
df = df.merge(r1, on="order_id", how="left", validate="one_to_one")

deliv, est = df["order_delivered_customer_date"], df["order_estimated_delivery_date"]
df["late"] = (deliv > est).astype(float).where(deliv.notna())   # NaN if not delivered

keep = ["order_id", "order_status", "customer_state", "order_purchase_timestamp",
        "order_delivered_customer_date", "order_estimated_delivery_date",
        "late", "review_score", "review_creation_date"]
os.makedirs("data/processed", exist_ok=True)
df[keep].to_csv("data/processed/orders_fact.csv", index=False)

print("== integrity ==")
print("rows:", len(df), "| unique order_id:", df["order_id"].nunique())
print("orders with >1 review (before dedup):", multi)
print("orders with no review:", int(df["review_score"].isna().sum()))
print("missing customer_state:", int(df["customer_state"].isna().sum()))
print("delivered before purchase:", int((deliv < df["order_purchase_timestamp"]).sum()))
print("estimated before purchase:", int((est < df["order_purchase_timestamp"]).sum()))
print("no delivery date:", int(deliv.isna().sum()), "| of those, status delivered:",
      int((deliv.isna() & (df["order_status"] == "delivered")).sum()))
print("estimated date at midnight:", f"{(est.dt.hour == 0).mean():.0%}")

print("\n== reconcile with weekly_signals.csv (max abs difference) ==")
old = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
ow = df.set_index("order_purchase_timestamp").resample("W").size()
lw = df.dropna(subset=["order_delivered_customer_date"]).set_index("order_delivered_customer_date")["late"].resample("W").mean()
sw = df.dropna(subset=["review_creation_date"]).set_index("review_creation_date")["review_score"].resample("W").mean()
print("orders    :", (ow.reindex(old.index) - old["orders"]).abs().max())
print("pct_late  :", (lw.reindex(old.index) - old["pct_late"]).abs().max())
print("avg_score :", round((sw.reindex(old.index) - old["avg_score"]).abs().max(), 4))