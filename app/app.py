import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="PULSE", layout="wide")

@st.cache_data
def load():
    sig = pd.read_csv("data/processed/weekly_signals.csv", index_col=0, parse_dates=True)
    report = json.load(open("data/processed/report.json"))
    inv = {r["id"]: r for r in json.load(open("data/processed/investigation.json"))}
    return sig, report, inv

sig, report, inv = load()
COLORS = {"HIGH": "#d62728", "MEDIUM": "#ff7f0e", "LOW": "#999999"}
LABELS = {"orders": "Weekly orders", "avg_score": "Average review score", "pct_late": "Late deliveries (%)"}

st.title("PULSE: business early-warning system")
st.caption("Detects unusual weeks, traces them to a cause, and recommends where to look first.")

c1, c2, c3 = st.columns(3)
c1.metric("Events detected", len(report))
c2.metric("High severity", sum(r["severity"] == "HIGH" for r in report))
c3.metric("Weeks monitored", len(sig))

signal = st.radio("Signal", list(LABELS), format_func=LABELS.get, horizontal=True)
y = sig[signal] * (100 if signal == "pct_late" else 1)

fig = go.Figure(go.Scatter(x=sig.index, y=y, mode="lines", name=LABELS[signal]))
for r in report:
    x0 = pd.Timestamp(r["start"]) - pd.Timedelta(days=6)
    fig.add_vrect(x0=str(x0.date()), x1=r["end"], fillcolor=COLORS[r["severity"]],
                  opacity=0.25, line_width=0, annotation_text=f"#{r['id']}",
                  annotation_position="top left")
fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), yaxis_title=LABELS[signal])
st.plotly_chart(fig, use_container_width=True)
st.caption("Shaded bands are detected events: red = high, orange = medium, grey = low.")

st.subheader("Event investigation")
ids = [r["id"] for r in report]
pick = st.selectbox("Event", ids, index=min(3, len(ids) - 1),
                    format_func=lambda i: next(f"#{r['id']}  {r['start']} to {r['end']}  ({r['severity']})"
                                               for r in report if r["id"] == i))
r = next(x for x in report if x["id"] == pick)

st.markdown(f"**{r['headline']}**")
st.markdown(f"**Pattern:** {r['kind']}")
if "reliability" in r:
    st.markdown(f"**Reliability:** {r['reliability']}")
st.info(f"Recommendation: {r['recommendation']}")

if inv[pick]["investigated"]:
    cols = st.columns(3)
    for col, name in zip(cols, ("regions", "categories", "sellers")):
        col.markdown(f"**Top {name}**")
        for g in inv[pick][name]["strongest_abnormal_change"]:
            col.write(f"- {g['group'][:12]}: {g['late_base_pct']}% to {g['late_event_pct']}% "
                      f"({g['excess_share_pct']}% of excess late)")
    if r.get("repeat_sellers"):
        st.warning("Repeat offender sellers: " + ", ".join(s[:8] for s in r["repeat_sellers"]))
else:
    st.write("Late deliveries were not behind this event, so no drill-down was run.")