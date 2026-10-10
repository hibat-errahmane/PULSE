# PULSE — Multi-Signal Business Early-Warning System

**PULSE helps businesses detect unusual operational patterns early and prioritize where to investigate.**

Businesses often monitor orders, delivery performance, and customer satisfaction separately. PULSE combines these signals in one dashboard to highlight unusual changes, explore potential hotspots, and support data-driven investigations.

## Features

- **Multi-signal anomaly detection:** analyzes weekly order volume, review scores, and late-delivery rates using a robust statistical baseline.
- **Event detection:** groups unusual periods and assigns severity and confidence indicators.
- **Forecasting:** provides short-term projections to help users monitor business trends.
- **Evidence-based investigation:** explores delivery issues by region, seller, and product category, with safeguards for small samples.
- **Actionable dashboard:** presents historical signals, forecasts, evidence summaries, and investigation priorities in Streamlit.
- **Synthetic evaluation:** tests detection behavior against simulated demand and fulfillment scenarios.

## Dataset

PULSE uses the Olist Brazilian e-commerce dataset, available through Kaggle.

- **Coverage:** approximately March 2017 – August 2018.
- **Signals:** weekly orders, review scores, and late-delivery rate.
- **Data directory:** `data/raw/olist/`

The processed data and generated results are included in the project for dashboard demonstration.

## Getting Started

### Requirements
- Python 3.10 or later
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Launch the dashboard

If the processed outputs in `data/processed/` are already available, run:

```bash
streamlit run app/app.py
```

### Rebuild the analysis

To regenerate the results from the raw dataset, run:

```bash
python src/investigate.py
python src/report.py
python src/forecast.py
```

Run the analysis scripts from the project root. The raw dataset must be placed in the expected directory first.

## Example Findings

The analysis highlights several periods worth investigating:

- **December 2017 – January 2018:** late-delivery rates increased from approximately 5.1% to 14.5%.
- **March – April 2018:** late-delivery rates increased from approximately 9.7% to 22%.
- **August 2018:** the analysis identified a more geographically concentrated delivery issue.
- **Recurring seller patterns:** some sellers appeared among the leading contributors across multiple detected events.

These are findings from the analyzed dataset, not proof of the underlying causes.

## Evaluation

PULSE includes synthetic experiments to compare different signal combinations under simulated demand and fulfillment events. Results depend on the tested scenarios and should not be interpreted as guaranteed real-world detection performance.

## Limitations

- The demonstration uses one historical e-commerce dataset.
- Statistical anomalies indicate unusual behavior, not causation.
- Recommendations are rule-based; PULSE does not use an LLM to generate its conclusions.
- Small groups and events are treated cautiously to reduce misleading conclusions.
- Testing many groups can produce false positives, so investigation flags require human review.

## Tech Stack

Python · Pandas · Plotly · Streamlit · Statistical anomaly detection

## Project Goal

PULSE turns multiple business signals into an early-warning and investigation workflow, helping users decide **what to investigate first** without claiming to automatically determine why a problem occurred.