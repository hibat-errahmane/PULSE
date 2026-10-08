import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
import numpy as np
import pandas as pd
from drilldown import P, drill, show

f = pd.read_csv("data/processed/orders_fact.csv",
                parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                             "order_estimated_delivery_date", "review_creation_date"])
items = pd.read_csv(P + "olist_order_items_dataset.csv", usecols=["order_id", "product_id"])
prod = pd.read_csv(P + "olist_products_dataset.csv", usecols=["product_id", "product_category_name"])
tr = pd.read_csv(P + "product_category_name_translation.csv")

m = items.merge(prod, on="product_id", how="left", validate="many_to_one")
m = m.merge(tr, on="product_category_name", how="left", validate="many_to_one")
m["category"] = m["product_category_name_english"].fillna(m["product_category_name"]).fillna("unknown")
cats = m[["order_id", "category"]].drop_duplicates()
nc = cats.groupby("order_id")["category"].transform("nunique")

n_orders_items = cats["order_id"].nunique()
print("== reliability check ==")
print("orders with items:", n_orders_items, "of", len(f))
print("orders with exactly 1 category:", f"{(nc[~cats['order_id'].duplicated()] == 1).mean():.1%}")
print("orders with 2+ categories (excluded):", int((nc[~cats['order_id'].duplicated()] > 1).sum()))
print("single-category orders with unknown category:", int(((nc == 1) & (cats['category'] == 'unknown')).sum()))
print("distinct categories:", cats["category"].nunique(), "\n")

single = cats[nc == 1]
f = f.merge(single, on="order_id", how="left", validate="one_to_one")
f["category"] = f["category"].replace("unknown", np.nan)

table, totals = drill(f, "category", "2017-12-17", "2018-01-14")
show(table, totals, "category")