# Airflow integration — Customer Analytics Task 9

## DAG

- **DAG id:** `customer_analytics_etl_task9`
- **Schedule:** daily 06:00 UTC
- **Tasks:**
  1. `check_source_file` — raw CSV present
  2. `etl_transform_load_quality` — full ETL + quality gate (**fails on ALERT**)
  3. `analyze_alert_thresholds` — refresh threshold analysis
  4. `publish_clean_marker` — write publish marker for consumers

## Deploy

```bash
# Copy project onto the worker
export AIRFLOW_HOME=/opt/airflow
git clone https://github.com/koffifidelek59-collab/customer-analytics.git /opt/airflow/project/customer-analytics

# Register DAG
cp airflow/customer_analytics_etl_dag.py $AIRFLOW_HOME/dags/

# Optional: set project root Variable in Airflow UI
# CUSTOMER_ETL_ROOT = /opt/airflow/project/customer-analytics
```

## Quality gate

The ETL task raises if quality status is `ALERT` (exit code 2), blocking publish.

Threshold policy: see `results/ALERT_THRESHOLDS_ANALYSIS.md`.

## Local test without Airflow

```bash
python etl/run_etl.py
python api/run_quality_alerts.py
```
