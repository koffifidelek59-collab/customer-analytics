# Customer Analytics — Task 10

## Data Quality, Measures and Decision Support on 2,100 Customers

This project presents an end-to-end **customer analytics and data quality workflow**, from raw data ingestion to analytical insights and decision-support tools.

The workflow follows a reproducible data pipeline:

**Raw Data → Data Audit → Data Cleaning → KPIs & Measures → Statistical Analysis → Insights → Interactive Dashboard → Automated Data Quality Monitoring**

The objective is not only to analyse customer purchasing behaviour, but also to assess the **reliability, completeness and consistency of the underlying data** before using it for decision-making.

---

## Author

**KOUAME Koffi Fidèle**
WASCAL IMP-EGH — Abdou Moumouni University
Niamey, Niger

📧 [koffifidelek59@gmail.com](mailto:koffifidelek59@gmail.com)

---

## Access the Notebook

Run the complete analysis directly in Google Colab:

<a target="_blank" href="https://colab.research.google.com/github/koffifidelek59-collab/customer-analytics/blob/main/Customer-Analytics.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

**Estimated execution time:** less than 1 minute on a standard CPU.

---

## Project Objectives

The project addresses five main objectives:

1. **Audit the quality of the customer dataset**
2. **Clean and prepare the data for analysis while preserving quality flags**
3. **Calculate business and statistical measures**
4. **Identify relationships and patterns in customer spending**
5. **Build reproducible decision-support and data-quality monitoring tools**

A key principle of this project is that **data quality must be evaluated before analytical conclusions are made**.

---

## Dataset

The final analytical dataset contains:

* **2,100 customers**
* **$1,021,324 total recorded revenue**
* **$509.90 average transaction value**
* **$519.42 median transaction value**
* **2,003 recorded purchase amounts**

The cleaning process removed **50 exact duplicate records** while retaining relevant data-quality flags for further analysis.

---

## Data Quality Assessment

The analysis identified several important data-quality issues.

| Data quality issue           |        Observation |
| ---------------------------- | -----------------: |
| Final customer records       |              2,100 |
| Exact duplicate rows removed |                 50 |
| Usable age values            |              23.6% |
| Invalid age sentinel values  |         −1 and 200 |
| Rating values equal to 10    |                291 |
| Sentinel dates               |                118 |
| Missing categories           |              26.9% |
| Phone numbers                | Placeholder values |
| Email addresses              | Placeholder values |

These findings show that **data capture and data validation are major analytical considerations**.

Instead of silently deleting problematic observations, the workflow keeps explicit quality flags where appropriate so that downstream users can distinguish between valid observations, missing information and suspicious values.

---

## Statistical Analysis

The project uses statistical tests to determine whether available customer attributes are associated with spending.

The analysis examined:

* Product category
* Gender
* Age
* Customer rating

### Main statistical results

| Variable | Statistical result |
| -------- | -----------------: |
| Category |           p = 0.45 |
| Gender   |           p = 0.10 |
| Age      |           ρ = 0.02 |
| Rating   |          ρ = −0.03 |

Within this dataset and under the statistical tests applied, **no analysed customer attribute showed a statistically significant relationship with spending**.

These results should be interpreted as findings for this dataset and analytical sample, rather than as general conclusions about customer behaviour in other populations.

---

## Customer Satisfaction

Customer ratings indicate a moderate level of reported satisfaction.

* **Mean rating:** 3.03 / 5
* **Ratings of 1 or 2:** 38.7%
* **Ratings equal to 10:** 291 records, identified as a data-quality issue

The analysis therefore separates the **observed rating distribution** from potentially invalid or anomalous values.

---

## Seasonality Analysis

Monthly purchasing patterns were also investigated.

The statistical analysis found:

* **32 complete months** available for the analysis
* **p = 0.11** for the seasonality test

The apparent August–September decline in the pooled monthly visualization is therefore interpreted cautiously.

Rather than automatically treating the decrease as a seasonal effect, the analysis identifies **data coverage as a possible explanation**.

This illustrates an important analytical principle:

> A visible pattern in a chart does not necessarily represent a real behavioural effect.

---

## Main Findings

### 1. Data quality is a primary limitation

The customer register contains substantial missing, placeholder and anomalous values. Consequently, data-quality assessment is an essential step before interpreting customer behaviour.

### 2. Customer attributes show limited explanatory power

Category, gender, age and rating do not provide statistically significant evidence of association with spending in the analysed dataset.

### 3. Customer satisfaction requires attention

The mean rating is **3.03/5**, with **38.7% of ratings equal to 1 or 2**, indicating a substantial proportion of low reported ratings.

### 4. Apparent monthly patterns require contextual interpretation

The August–September decline observed in the pooled monthly visualization should not automatically be interpreted as seasonality because the available data coverage varies.

### 5. Data quality monitoring should be continuous

The project therefore extends beyond a one-time analysis by implementing automated quality checks, alerts and monitoring components.

---

## Deliverables

| Deliverable                       | File / Directory           |
| --------------------------------- | -------------------------- |
| Complete analysis notebook        | `Customer-Analytics.ipynb` |
| Formal analytical report          | `report.pdf`               |
| Report source                     | `report.tex`               |
| Interactive dashboard             | `dashboard.html`           |
| Raw customer register             | `data/customers_raw.csv`   |
| Clean customer register           | `data/customers_clean.csv` |
| Data dictionary                   | `data/DATA_DICTIONARY.md`  |
| KPI and statistical result tables | `results/`                 |
| Analysis figures                  | `figures/`                 |
| Dashboard screenshots             | `figures/dashboard/`       |
| ETL pipeline                      | `etl/run_etl.py`           |
| Quality gate and alerts           | `api/`                     |
| Airflow orchestration             | `airflow/`                 |
| Grafana monitoring                | `grafana/`                 |
| Container configuration           | `docker-compose.yml`       |

---

## Repository Structure

```text
customer-analytics/
│
├── data/
│   ├── customers_raw.csv
│   ├── customers_clean.csv
│   └── DATA_DICTIONARY.md
│
├── figures/
│   ├── analysis figures
│   └── dashboard/
│       └── dashboard captures
│
├── results/
│   ├── KPIs
│   ├── statistical tests
│   ├── aggregates
│   └── quality alerts
│
├── etl/
│   └── run_etl.py
│
├── api/
│   ├── quality gate
│   ├── notifications
│   └── Prometheus metrics
│
├── airflow/
│   └── daily ETL and quality-control DAG
│
├── grafana/
│   ├── Prometheus configuration
│   └── provisioned dashboard
│
├── Customer-Analytics.ipynb
├── dashboard.html
├── report.pdf
├── report.tex
├── docker-compose.yml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Analytical Workflow

```text
                    RAW CUSTOMER DATA
                           │
                           ▼
                    DATA QUALITY AUDIT
                           │
                           ▼
                    DATA CLEANING
                           │
                           ▼
                 CLEAN DATA + QUALITY FLAGS
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        KPI CALCULATION          STATISTICAL TESTS
              │                         │
              └────────────┬────────────┘
                           ▼
                    ANALYTICAL INSIGHTS
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     INTERACTIVE DASHBOARD       QUALITY MONITORING
                                        │
                                        ▼
                              ALERTS & NOTIFICATIONS
```

---

## Reproducibility

Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

Execute the notebook:

```bash
jupyter nbconvert --to notebook --execute --inplace Customer-Analytics.ipynb
```

Compile the analytical report:

```bash
pdflatex report.tex
pdflatex report.tex
```

---

## ETL Pipeline

The ETL process can be executed independently:

```bash
python etl/run_etl.py
```

The pipeline performs:

```text
Extract → Transform → Load → Audit
```

It produces the cleaned analytical dataset while documenting relevant quality indicators.

---

## Automated Quality Monitoring

Run the quality gate:

```bash
python api/run_quality_alerts.py
```

Exit codes:

```text
0 = OK
1 = WARN
2 = ALERT
```

Run quality checks and notifications:

```bash
python api/run_quality_and_notify.py
```

Notifications can be directed to supported outputs such as:

* Console
* File
* Webhook
* Email

---

## Monitoring Stack

Prometheus metrics can be exposed using:

```bash
python api/metrics_server.py --port 9108
```

Then start the monitoring services:

```bash
docker compose up -d
```

The monitoring architecture combines:

**ETL → Quality Gate → Metrics → Prometheus → Grafana**

This allows data-quality indicators to be monitored continuously rather than only during the initial analysis.

---

## Dashboard

The project includes an interactive dashboard containing **nine analytical views**.

The dashboard provides a visual interface for exploring:

* Customer characteristics
* Revenue distribution
* Purchase behaviour
* Ratings
* Category patterns
* Temporal trends
* Data-quality indicators
* Statistical findings
* Decision-support information

The dashboard is available in:

```text
dashboard.html
```

---

## Technology Stack

### Data Analysis

* Python
* Pandas
* NumPy
* SciPy
* Matplotlib
* Jupyter Notebook

### Data Engineering

* ETL pipeline
* Data validation
* Quality gates
* Automated alerts

### Visualization & Monitoring

* Interactive HTML dashboard
* Prometheus
* Grafana

### Orchestration & Deployment

* Apache Airflow
* Docker
* Docker Compose

### Reporting

* LaTeX
* PDF

---

## Scientific and Analytical Approach

The project follows a reproducible analytical methodology:

**Data → Evidence → Statistical Analysis → Interpretation → Decision Support**

Particular attention is given to distinguishing:

* observed values from validated values,
* missing data from zero values,
* anomalous values from genuine observations,
* visual patterns from statistically supported effects,
* statistical association from causal interpretation.

This approach reduces the risk of drawing misleading conclusions from poor-quality data.

---

## Limitations

The results should be interpreted within the limitations of the available dataset.

Important limitations include:

* substantial missing values,
* placeholder contact information,
* anomalous age and rating values,
* incomplete temporal coverage,
* missing product categories,
* limited information about the data-generation process.

Therefore, the findings describe the analysed dataset and should not automatically be generalized to other customer populations.

---

## Conclusion

This project demonstrates a complete workflow for transforming a customer purchase register into a **reproducible and monitored decision-support system**.

Rather than treating data analysis as only a visualization task, the project integrates:

**Data Quality + Data Engineering + Statistical Analysis + Visualization + Monitoring**

The resulting architecture provides a foundation for more reliable customer analytics and can be extended to larger datasets, automated reporting and production-grade data-quality monitoring.

---

## License

This project is released under the [MIT License](LICENSE).
