# Customer Analytics (Task 10) - Data Quality, Measures and Decision Support on 2,100 Customers

This project takes the customer purchase register from **raw data** to **decision support**:
raw data → clean data → measures & KPIs → statistical tests → insights → interactive dashboard → automated quality alerts.

Author:
- KOUAME Koffi Fidèle - WASCAL IMP-EGH, Abdou Moumouni University, Niamey, [koffifidelek59@gmail.com](mailto:koffifidelek59@gmail.com)

## Access this notebook

<a target="_blank" href="https://colab.research.google.com/github/koffifidelek59-collab/customer-analytics/blob/main/Customer-Analytics.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

Estimated time to execute end-to-end: under 1 minute on a CPU.

## Deliverables

| Deliverable | File |
|---|---|
| Analysis notebook (audit, cleaning, KPIs, figures, tests, insights) | `Customer-Analytics.ipynb` |
| Formal report with dashboard captures | `report.pdf` (source `report.tex`) |
| Interactive dashboard, nine views (unchanged) | `dashboard.html` |
| Raw register | `data/customers_raw.csv` |
| Clean register, 2,100 rows, quality flags kept | `data/customers_clean.csv`, `data/DATA_DICTIONARY.md` |
| Result tables (KPIs, tests, aggregates, alerts) | `results/` |
| Eight analysis figures, PNG 300 dpi | `figures/` |
| Dashboard captures inserted in the report | `figures/dashboard/` |
| ETL pipeline | `etl/run_etl.py` |
| Quality gate, notifications, metrics | `api/` |
| Scheduling and monitoring | `airflow/`, `grafana/`, `docker-compose.yml` |

## Repository structure

```
customer-analytics/
├── data/            raw and clean registers, data dictionary
├── figures/         eight analysis figures + dashboard captures (figures/dashboard/)
├── results/         KPIs, statistical tests, aggregates, quality alerts
├── etl/             Extract-Transform-Load pipeline with audit
├── api/             quality gate, notifications, Prometheus metrics
├── airflow/         daily DAG (ETL + quality gate)
├── grafana/         Prometheus config and provisioned dashboard
├── Customer-Analytics.ipynb
├── dashboard.html
├── report.pdf / report.tex
├── docker-compose.yml
├── requirements.txt
├── LICENSE
└── README.md
```

## Main findings

1. **2,100 customers** after removing 50 exact duplicate rows; revenue **$1,021,324**, average ticket **$509.90** (median $519.42) on 2,003 recorded amounts.
2. **Data capture is the first problem.** Only 23.6% of ages are usable (sentinels −1 and 200), 291 ratings equal 10, 118 dates are the sentinel 32/13/2020, 26.9% of categories are missing, and the phone and email fields are placeholders.
3. **No attribute predicts spending**: category (p = 0.45), gender (p = 0.10), age (ρ = 0.02) and rating (ρ = −0.03).
4. **Satisfaction is mediocre**: mean rating 3.03 / 5, 38.7% of ratings are 1 or 2.
5. **No seasonality** (p = 0.11 on 32 complete months): the August-September dip of the pooled monthly chart is a coverage effect.

## Reproduce

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace Customer-Analytics.ipynb
pdflatex report.tex && pdflatex report.tex
```

Pipeline and quality gate:

```bash
python etl/run_etl.py                 # Extract → Transform → Load + audit
python api/run_quality_alerts.py      # exit 0 = OK, 1 = WARN, 2 = ALERT
python api/run_quality_and_notify.py  # alerts to console / file / webhook / email
python api/metrics_server.py --port 9108 && docker compose up -d   # Prometheus + Grafana
```

## Tools

Python (pandas, NumPy, SciPy, Matplotlib), Jupyter, FastAPI, Airflow, Prometheus, Grafana, Docker, LaTeX.

## License

Released under the [MIT License](LICENSE).
