
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────────────────────────
# Project paths
# ─────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="PULSE",
    page_icon="📈",
    layout="wide",
)


# ─────────────────────────────────────────────
# Load project data
# ─────────────────────────────────────────────

@st.cache_data
def load():

    sig = pd.read_csv(
        ROOT / "data" / "processed" / "weekly_signals.csv",
        index_col=0,
        parse_dates=True,
    )

    with open(
        ROOT / "data" / "processed" / "report.json",
        "r",
        encoding="utf-8",
    ) as f:
        report = json.load(f)

    with open(
        ROOT / "data" / "processed" / "evidence.json",
        "r",
        encoding="utf-8",
    ) as f:
        evidence = json.load(f)

    with open(
        ROOT / "data" / "processed" / "investigation.json",
        "r",
        encoding="utf-8",
    ) as f:
        inv = json.load(f)

    forecast_path = ROOT / "data" / "processed" / "forecast.csv"

    if forecast_path.exists():
        forecast = pd.read_csv(
            forecast_path,
            index_col=0,
            parse_dates=True,
        )
    else:
        forecast = pd.DataFrame()

    evaluation_path = ROOT / "results" / "experiments_fair.csv"

    if evaluation_path.exists():
        evaluation = pd.read_csv(
            evaluation_path,
            index_col=0,
        )
    else:
        evaluation = pd.DataFrame()

    evidence_by_id = {}

    for event in evidence.get("events", []):
        evidence_by_id[str(event.get("id"))] = event

    return (
        sig,
        report,
        inv,
        forecast,
        evidence_by_id,
        evaluation,
    )


(
    sig,
    report,
    inv,
    forecast,
    evidence_by_id,
    evaluation,
) = load()


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────

st.title("PULSE: business early-warning system")

st.caption(
    "Detects unusual weeks, traces them to investigation leads, "
    "and recommends where to look first."
)

st.info(
    "PULSE identifies statistical anomalies and investigation priorities. "
    "It does not establish causation."
)


# ─────────────────────────────────────────────
# Executive Summary
# ─────────────────────────────────────────────

st.divider()
st.header("1. Executive Summary")

events = report if isinstance(report, list) else report.get("events", [])

high_count = sum(
    1
    for e in events
    if str(e.get("severity", "")).upper() == "HIGH"
)

weeks_monitored = len(sig)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Events detected", len(events))

with c2:
    st.metric("High severity", high_count)

with c3:
    st.metric("Weeks monitored", weeks_monitored)

if events:
    priority = next(
        (
            e for e in events
            if str(e.get("severity", "")).upper() == "HIGH"
        ),
        events[0],
    )

    st.subheader(f"Priority event: Event #{priority.get('id')}")

    st.write(
        priority.get(
            "headline",
            priority.get(
                "summary",
                priority.get("description", "Priority anomaly detected."),
            ),
        )
    )

    st.markdown("### Recommended investigation")

    st.write(
        priority.get(
            "recommendation",
            "Review the event evidence and investigate the largest hotspots first.",
        )
    )


# ─────────────────────────────────────────────
# Business Signals + Forecast
# ─────────────────────────────────────────────

st.divider()
st.header("2. Business Signals + Forecast")

signal_options = {
    "Weekly orders": "orders",
    "Average review score": "avg_score",
    "Late deliveries (%)": "pct_late",
}

signal_label = st.radio(
    "Signal",
    list(signal_options.keys()),
    horizontal=True,
)

signal_col = signal_options[signal_label]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=sig.index,
        y=sig[signal_col],
        mode="lines",
        name=signal_label,
    )
)

fig.update_layout(
    height=420,
    xaxis_title="Week",
    yaxis_title=signal_label,
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Detected-event periods are highlighted conceptually in the event investigation below."
)

if not forecast.empty and signal_col in forecast.columns:
    st.subheader("Forecast")

    forecast_fig = go.Figure()

    forecast_fig.add_trace(
        go.Scatter(
            x=forecast.index,
            y=forecast[signal_col],
            mode="lines",
            name=f"{signal_label} forecast",
        )
    )

    forecast_fig.update_layout(
        height=350,
        xaxis_title="Week",
        yaxis_title=signal_label,
    )

    st.plotly_chart(forecast_fig, use_container_width=True)

else:
    st.caption("Forecast data is not available for this signal.")


# ─────────────────────────────────────────────
# Event Investigation
# ─────────────────────────────────────────────

st.divider()
st.header("3. Event Investigation")

pick = None
selected = None

if events:
    event_labels = []

    for e in events:
        event_labels.append(
            f"#{e.get('id')}  "
            f"{e.get('start')} to {e.get('end')}  "
            f"({str(e.get('severity', '')).upper()})"
        )

    selected_label = st.selectbox("Event", event_labels)

    selected_index = event_labels.index(selected_label)
    selected = events[selected_index]
    pick = selected.get("id")

    st.subheader(f"Event #{pick}")

    st.write(
        selected.get(
            "headline",
            selected.get(
                "summary",
                selected.get("description", "Anomaly detected."),
            ),
        )
    )

    st.write(f"**Severity:** {selected.get('severity', 'N/A')}")

    st.write(
        f"**Confidence:** "
        f"{selected.get('confidence', selected.get('reliability', 'N/A'))}"
    )

    pattern = selected.get("kind", selected.get("pattern", "N/A"))
    st.write(f"**Pattern:** {str(pattern).replace('_', ' ').title()}")
    st.write(
        selected.get(
            "recommendation",
            "Review the supporting evidence.",
        )
    )

else:
    st.warning("No events were detected.")


# ─────────────────────────────────────────────
# Signal Evidence
# ─────────────────────────────────────────────

st.divider()
st.header("Signal Evidence")

st.caption(
    "Baseline values are compared with event-period averages. "
    "Anomaly scores measure statistical unusualness, not causation."
)

event_evidence = (
    evidence_by_id.get(str(pick), {})
    if pick is not None
    else {}
)

facts = event_evidence.get("facts", {})

if not isinstance(facts, dict):
    facts = {}

signal_fact_map = {
    "Weekly orders": ("orders", "Orders"),
    "Average review score": ("avg_score", "Average review score"),
    "Late deliveries (%)": ("pct_late", "Late deliveries (%)"),
}

if facts:
    evidence_rows = []

    for label, (key, _) in signal_fact_map.items():
        item = facts.get(key, {})

        if isinstance(item, dict):
            evidence_rows.append(
                {
                    "Signal": label,
                    "Baseline": item.get("baseline", "N/A"),
                    "Event average": item.get("event_mean", "N/A"),
                    "Change": item.get("change", "N/A"),
                    "Unit": item.get("unit", "N/A"),
                }
            )

    if evidence_rows:
        st.dataframe(
            pd.DataFrame(evidence_rows),
            use_container_width=True,
            hide_index=True,
        )


# ─────────────────────────────────────────────
# Investigation Drill-down
# ─────────────────────────────────────────────

st.divider()
st.header("4. Investigation Drill-down")

investigation = {}

if pick is not None and inv:
    try:
        event_number = int(pick)

        if isinstance(inv, list) and 1 <= event_number <= len(inv):
            investigation = inv[event_number - 1]

        elif isinstance(inv, dict):
            investigation = inv.get(
                str(pick),
                inv.get(event_number, {}),
            )

    except (TypeError, ValueError):
        investigation = {}

if isinstance(investigation, dict) and investigation:
    st.write(
        investigation.get(
            "summary",
            "Investigation details are available.",
        )
    )

    for key in ["regions", "categories", "sellers"]:
        values = investigation.get(key, [])

        if values:
            st.subheader(key.replace("_", " ").title())
            st.json(values)

else:
    st.write("No additional drill-down information is available.")


# ─────────────────────────────────────────────
# Detection Evaluation
# ─────────────────────────────────────────────

st.divider()
st.header("5. Detection Evaluation")

st.caption(
    "Detection rate on synthetic events injected into the real weekly series. "
    "The experiment tests whether adding multiple business signals improves "
    "detection of fulfillment problems."
)

if not evaluation.empty:
    evaluation_display = evaluation.rename(
        columns={
            "valid_starts": "Valid starts",
            "demand_30": "Demand events (%)",
            "fulfil_weak": "Fulfillment — weak (%)",
            "fulfil_strong": "Fulfillment — strong (%)",
        }
    )

    st.dataframe(
        evaluation_display,
        use_container_width=True,
    )

    st.markdown(
        """
**What this shows**

- **Orders only:** detects demand anomalies, but cannot detect
  fulfillment problems because it does not observe fulfillment signals.
- Adding **late deliveries** substantially improves fulfillment detection.
- Adding **review score** also improves detection.
- Using **all three signals** reaches **100% detection on the strong
  synthetic fulfillment events** in this experiment.

These results are evidence that PULSE benefits from monitoring multiple
signals rather than relying on orders alone.
"""
    )

else:
    st.warning("Evaluation results are not available yet.")


# ─────────────────────────────────────────────
# Alert Timeline
# ─────────────────────────────────────────────

st.divider()
st.header("6. Alert Timeline")

if events:
    timeline_rows = []

    severity_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    for e in events:
        severity = str(e.get("severity", "LOW")).upper()

        timeline_rows.append(
            {
                "Event": f"#{e.get('id')}",
                "Start": e.get("start"),
                "End": e.get("end"),
                "Severity": severity,
                "Confidence": e.get("confidence", e.get("reliability", "N/A")),
		"Pattern": str(e.get("kind", e.get("pattern", "N/A"))).replace("_", " ").title(),
                "_order": severity_order.get(severity, 3),
            }
        )

    timeline = pd.DataFrame(timeline_rows)

    timeline = timeline.sort_values(
        ["_order", "Start"]
    ).drop(columns=["_order"])

    st.dataframe(
        timeline,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("No alerts available.")


# ─────────────────────────────────────────────
# Intelligence Brief
# ─────────────────────────────────────────────

st.divider()
st.header("7. Intelligence Brief")

st.caption(
    "Generated deterministically from measured PULSE signals. "
    "It does not invent causes."
)

if facts:
    orders_fact = facts.get("orders", {})
    score_fact = facts.get("avg_score", {})
    late_fact = facts.get("pct_late", {})

    orders_change = (
        orders_fact.get("change", 0)
        if isinstance(orders_fact, dict)
        else 0
    )

    score_change = (
        score_fact.get("change", 0)
        if isinstance(score_fact, dict)
        else 0
    )

    late_change = (
        late_fact.get("change", 0)
        if isinstance(late_fact, dict)
        else 0
    )

    brief = []

    try:
        orders_change = float(orders_change)

        if orders_change <= -0.10:
            brief.append("Demand deterioration detected.")
        elif orders_change >= 0.10:
            brief.append("Demand increase detected.")

    except (TypeError, ValueError):
        pass

    try:
        score_change = float(score_change)

        if score_change <= -0.20:
            brief.append("Customer sentiment weakened.")
        elif score_change >= 0.20:
            brief.append("Customer sentiment improved.")

    except (TypeError, ValueError):
        pass

    try:
        late_change = float(late_change)

        if late_change >= 2:
            brief.append("Fulfillment performance deteriorated.")
        elif late_change <= -2:
            brief.append("Fulfillment performance improved.")

    except (TypeError, ValueError):
        pass

    if brief:
        for item in brief:
            st.write(f"• {item}")
    else:
        st.write(
            "No strong directional change crossed the briefing thresholds."
        )

else:
    st.write("No event facts are available for the intelligence brief.")


# ─────────────────────────────────────────────
# What-if Business Simulator
# ─────────────────────────────────────────────

st.divider()
st.header("8. What-if Business Simulator")

st.caption(
    "Explore hypothetical signal changes. "
    "This is not a prediction and does not rerun the anomaly detector."
)

col1, col2, col3 = st.columns(3)

with col1:
    orders_delta = st.slider(
        "Weekly orders change (%)",
        -50,
        50,
        0,
        5,
    )

with col2:
    score_delta = st.slider(
        "Average review score change",
        -2.0,
        2.0,
        0.0,
        0.1,
    )

with col3:
    late_delta = st.slider(
        "Late deliveries change (pp)",
        -15,
        15,
        0,
        1,
    )

orders_score = min(abs(orders_delta) / 30, 1)
score_score = min(abs(score_delta) / 0.5, 1)
late_score = min(abs(late_delta) / 5, 1)

simulator_score = (
    0.35 * orders_score
    + 0.25 * score_score
    + 0.40 * late_score
) * 100

st.metric(
    "Hypothetical signal deviation",
    f"{simulator_score:.0f}/100",
)

st.progress(
    int(simulator_score),
    text="Higher = more unusual hypothetical change",
)


# ─────────────────────────────────────────────
# Explainable Risk Score
# ─────────────────────────────────────────────

st.divider()
st.header("9. Explainable Risk Score")

st.caption(
    "A transparent heuristic showing how strongly the selected event "
    "deviates across the monitored signals. It is not a probability "
    "of business failure."
)

risk_weights = {
    "Weekly orders": 0.35,
    "Average review score": 0.25,
    "Late deliveries (%)": 0.40,
}

risk_values = {
    "Weekly orders": 0.0,
    "Average review score": 0.0,
    "Late deliveries (%)": 0.0,
}

if facts:
    try:
        risk_values["Weekly orders"] = min(
            abs(float(facts["orders"]["change"])) / 0.30,
            1.0,
        )
    except (KeyError, TypeError, ValueError):
        pass

    try:
        risk_values["Average review score"] = min(
            abs(float(facts["avg_score"]["change"])) / 0.50,
            1.0,
        )
    except (KeyError, TypeError, ValueError):
        pass

    try:
        risk_values["Late deliveries (%)"] = min(
            abs(float(facts["pct_late"]["change"])) / 5.0,
            1.0,
        )
    except (KeyError, TypeError, ValueError):
        pass

risk_score = sum(
    risk_values[name] * risk_weights[name]
    for name in risk_values
) * 100

risk_score = min(max(risk_score, 0), 100)

risk_table = pd.DataFrame(
    {
        "Signal": list(risk_values.keys()),
        "Relative deviation": [
            round(value * 100, 1)
            for value in risk_values.values()
        ],
        "Weight (%)": [
            weight * 100
            for weight in risk_weights.values()
        ],
    }
)

st.dataframe(
    risk_table,
    use_container_width=True,
    hide_index=True,
)

risk_fig = go.Figure(
    go.Bar(
        x=risk_table["Relative deviation"],
        y=risk_table["Signal"],
        orientation="h",
    )
)

risk_fig.update_layout(
    height=300,
    xaxis_title="Relative deviation (%)",
    yaxis_title="",
    xaxis=dict(range=[0, 100]),
)

st.plotly_chart(
    risk_fig,
    use_container_width=True,
)

st.metric(
    "Signal deviation score",
    f"{risk_score:.0f}/100",
)

st.caption(
    "Illustrative thresholds and weights should be validated before "
    "operational use."
)


# ─────────────────────────────────────────────
# PULSE Health Score
# ─────────────────────────────────────────────

st.divider()
st.header("10. PULSE Health Score")

st.caption(
    "A simple inverse view of the explainable signal-deviation score."
)

health_score = max(0, min(100, 100 - risk_score))

if health_score >= 75:
    health_status = "HEALTHY"
elif health_score >= 50:
    health_status = "WATCH"
else:
    health_status = "AT RISK"

hc1, hc2 = st.columns(2)

with hc1:
    st.metric(
        "Business health score",
        f"{health_score:.0f}/100",
    )

with hc2:
    st.metric(
        "Current status",
        health_status,
    )

st.progress(
    int(health_score),
    text=f"Health: {health_score:.0f}/100 — {health_status}",
)


# ─────────────────────────────────────────────
# Action Center
# ─────────────────────────────────────────────

st.divider()
st.header("11. Action Center")

st.caption(
    "Create a concise incident report for investigation and follow-up."
)

if selected is not None:
    report_text = f"""# PULSE Incident Report

## Event

Event #{selected.get('id')}

## Period

{selected.get('start')} to {selected.get('end')}

## Severity

{selected.get('severity', 'N/A')}

## Pattern

{str(selected.get('kind', selected.get('pattern', 'N/A'))).replace('_', ' ').title()}

## Summary

{selected.get('headline', selected.get('summary', selected.get('description', 'N/A')))}
## Recommended next step

{selected.get('recommendation', 'Review the evidence and investigate the largest hotspots first.')}

## Measured evidence

"""

    if facts:
        for label, (key, _) in signal_fact_map.items():
            item = facts.get(key, {})

            if isinstance(item, dict):
                report_text += (
                    f"\n### {label}\n\n"
                    f"- Baseline: {item.get('baseline', 'N/A')}\n"
                    f"- Event average: {item.get('event_mean', 'N/A')}\n"
                    f"- Change: {item.get('change', 'N/A')} "
                    f"{item.get('unit', '')}\n"
                )

    report_text += """
## Investigation leads

Prioritize the largest regional, category, and seller deviations.

## Suggested verification

Check operational records, carrier capacity, seasonal effects,
seller performance, and other relevant business context before
assigning a root cause.

## Important limitation

PULSE identifies statistical anomalies and investigation priorities.
It does not establish causation.
"""

    st.download_button(
        label="Download incident report",
        data=report_text,
        file_name=f"pulse_event_{selected.get('id')}_report.md",
        mime="text/markdown",
    )


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────

st.divider()

st.caption(
    "PULSE is a decision-support prototype. "
    "It combines multivariate anomaly detection, evidence, "
    "forecasting, investigation drill-down, simulation, "
    "and explainable risk scoring. It does not establish root cause."
)
