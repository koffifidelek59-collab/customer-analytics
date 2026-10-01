"""
Customer Analytics — Task 9
Airflow DAG: daily ETL + quality gate + publish markers

Deploy: copy this file to $AIRFLOW_HOME/dags/
Requires: pandas, numpy on the worker image
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# Project root on the worker — override via Airflow Variable CUSTOMER_ETL_ROOT
DEFAULT_ROOT = "/opt/airflow/project/customer-analytics"


def _root() -> Path:
    try:
        return Path(Variable.get("CUSTOMER_ETL_ROOT", default_var=DEFAULT_ROOT))
    except Exception:
        return Path(DEFAULT_ROOT)


default_args = {
    "owner": "kouame.koffi.fidele",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_etl_callable():
    root = _root()
    sys.path.insert(0, str(root))
    from etl.run_etl import run

    source = root / "data" / "customers_raw.csv"
    out = root / "data" / "customers_clean.csv"
    audit = root / "results" / "etl_audit.json"
    quality = root / "results" / "quality_alerts.json"
    code = run(source, out, audit, quality)
    if code >= 2:
        raise RuntimeError(f"ETL quality gate ALERT (exit={code}). See {quality}")
    return {"exit_code": code, "clean": str(out)}


def run_threshold_analysis_callable():
    """Recompute threshold analysis document after ETL."""
    root = _root()
    sys.path.insert(0, str(root))
    # lightweight: invoke quality module only
    from etl.run_etl import extract, transform, run_quality_alerts
    import json
    from datetime import datetime, timezone

    clean = root / "data" / "customers_clean.csv"
    import pandas as pd

    if clean.exists():
        df = pd.read_csv(clean)
        audit = {"duplicate_ids_removed": 0, "invalid_dates": int(df["DateInvalid"].sum()) if "DateInvalid" in df.columns else 0}
    else:
        df, audit = transform(extract(root / "data" / "customers_raw.csv"))
    qa = run_quality_alerts(df, audit)
    (root / "results" / "quality_alerts.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    if qa["status"] == "ALERT":
        # still record analysis; DAG quality task already gates hard fail on ETL
        pass
    return qa["status"]


with DAG(
    dag_id="customer_analytics_etl_task9",
    description="Customer Analytics Task 9 — ETL, quality thresholds, publish",
    default_args=default_args,
    schedule_interval="0 6 * * *",  # daily 06:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["customer", "etl", "quality", "task9"],
) as dag:

    check_source = BashOperator(
        task_id="check_source_file",
        bash_command=f'test -f "{DEFAULT_ROOT}/data/customers_raw.csv" && echo "source OK"',
    )

    run_etl = PythonOperator(
        task_id="etl_transform_load_quality",
        python_callable=run_etl_callable,
    )

    analyze_thresholds = PythonOperator(
        task_id="analyze_alert_thresholds",
        python_callable=run_threshold_analysis_callable,
    )

    # Publish marker for dashboard consumers (path can be a shared volume)
    publish_marker = BashOperator(
        task_id="publish_clean_marker",
        bash_command=(
            f'mkdir -p "{DEFAULT_ROOT}/results" && '
            f'date -u +"published_at=%Y-%m-%dT%H:%M:%SZ" > "{DEFAULT_ROOT}/results/publish_marker.txt" && '
            f'echo "clean_path={DEFAULT_ROOT}/data/customers_clean.csv" >> "{DEFAULT_ROOT}/results/publish_marker.txt"'
        ),
    )

    check_source >> run_etl >> analyze_thresholds >> publish_marker
