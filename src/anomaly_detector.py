import pandas as pd
from sklearn.ensemble import IsolationForest

# Load business data
df = pd.read_csv("data/sales.csv")

# Features used by the model
features = df[["sales", "price", "inventory", "promotion"]]

# Create the anomaly detection model
model = IsolationForest(
    contamination=0.15,
    random_state=42
)

# Train the model
model.fit(features)

# Predict anomalies
df["anomaly"] = model.predict(features)

# -1 = anomaly
#  1 = normal

print(df[["date", "sales", "price", "promotion", "anomaly"]])