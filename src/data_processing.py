import os
import pandas as pd

P = "data/raw/olist/"
o = pd.read_csv(P + "olist_orders_dataset.csv", parse_dates=[
    "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
r = pd.read_csv(P + "olist_order_reviews_dataset.csv", parse_dates=["review_creation_date"])

orders = o.set_index("order_purchase_timestamp").resample("W").size().rename("orders")

score = r.set_index("review_creation_date").resample("W")["review_score"].agg(["mean", "size"])
score.columns = ["avg_score", "n_reviews"]

d = o.dropna(subset=["order_delivered_customer_date"]).copy()
d["late"] = d["order_delivered_customer_date"] > d["order_estimated_delivery_date"]
late = d.set_index("order_delivered_customer_date")["late"].resample("W").mean().rename("pct_late")

sig = pd.concat([orders, score, late], axis=1).loc["2017-03-01":"2018-08-31"]
os.makedirs("data/processed", exist_ok=True)
sig.to_csv("data/processed/weekly_signals.csv")

print(sig.shape)
print(sig.describe().round(2).to_string())
print(sig.sort_values("pct_late", ascending=False).head(5).round(2).to_string())
