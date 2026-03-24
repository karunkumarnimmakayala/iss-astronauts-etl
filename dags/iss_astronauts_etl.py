"""
Daily DAG that extracts current ISS crew data from the Open Notify API,
transforms and validates the records, then loads them into PostgreSQL.

Schedule : daily at 07:00 UTC
Retries  : 3 (with 5-minute delay)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from scripts.extract import fetch_astronauts
from scripts.transform import transform_astronauts
from scripts.load import load_astronauts

logger = logging.getLogger(__name__)

WAREHOUSE_CONN = {
    "host": "postgres-warehouse",
    "port": 5432,
    "dbname": "warehouse",
    "user": "warehouse",
    "password": "warehouse",
}

default_args = {
    "owner": "karunkumar",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def extract(**context) -> None:
    raw = fetch_astronauts()
    context["ti"].xcom_push(key="raw_payload", value=raw)
    logger.info("Extract complete. People in space: %d", raw["number"])


def transform(**context) -> None:
    raw = context["ti"].xcom_pull(key="raw_payload", task_ids="extract")
    records = transform_astronauts(raw)

    if not records:
        raise ValueError("Transform produced zero valid records — aborting pipeline.")

    context["ti"].xcom_push(key="records", value=records)
    context["ti"].xcom_push(key="people_in_space", value=raw["number"])
    logger.info("Transform complete. Valid records: %d", len(records))


def load(**context) -> None:
    records = context["ti"].xcom_pull(key="records", task_ids="transform")
    people_in_space = context["ti"].xcom_pull(key="people_in_space", task_ids="transform")
    dag_run_id = context["run_id"]

    rows = load_astronauts(
        records=records,
        conn_params=WAREHOUSE_CONN,
        dag_run_id=dag_run_id,
        people_in_space=people_in_space,
    )
    logger.info("Load complete. Rows inserted: %d", rows)


with DAG(
    dag_id="iss_astronauts_etl",
    description="Daily ETL: ISS crew from Open Notify API → PostgreSQL warehouse",
    schedule="0 7 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["etl", "api", "postgresql"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    extract_task >> transform_task >> load_task
