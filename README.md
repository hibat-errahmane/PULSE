# PULSE: AI business early-warning system

PULSE watches weekly business signals, detects unusual weeks, traces each one to its likely source, and recommends where to look first.

## What it does
1. Builds weekly signals from real e-commerce data (orders, review score, late-delivery rate).
2. Detects anomalous weeks with a robust z-score baseline and groups them into events with a severity.
3. Drills into each late-delivery event by seller, region and product category, using sample-size and significance rules so small groups are not over-read.
4. Turns the findings into a plain-English pattern (systemic, localized, hotspot) and a recommendation.
5. Shows everything in a Streamlit dashboard.

## Data
Olist Brazilian e-commerce dataset (Kaggle). Usable window: 2017-03 to 2018-08.
Download it into `data/raw/olist/`.

## Run
```
pip install -r requirements.txt
python src\investigate.py
python src\report.py
streamlit run app\app.py
```

## Key findings
- Dec 2017 to Jan 2018: late deliveries rose from 5.1% to 14.5%. The problem is systemic, with Rio de Janeiro the biggest hotspot (37% of excess late orders).
- Mar to Apr 2018: late deliveries rose from 9.7% to 22%, again broad, with Sao Paulo the largest share.
- Aug 2018: a localized problem, with Sao Paulo carrying about 93% of the excess.
- Two sellers appear as top offenders across several events.

## Limitations
- One dataset and one business signal family. Detection is statistical, not causal: PULSE says where to look, not why.
- Recommendations are rule-based. No LLM is used.
- Small events (about 1000 orders) are flagged as watch-only.
- With many groups tested, a few flags happen by chance. The drill-down prints this expected rate.