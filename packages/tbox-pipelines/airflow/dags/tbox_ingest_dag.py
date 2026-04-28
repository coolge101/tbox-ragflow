"""S1 scaffold DAG for TBOX ingestion pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="tbox_ingest_scaffold",
    start_date=datetime(2026, 1, 1),
    schedule="0 */6 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["tbox", "ragflow", "s1"],
):
    # S1 uses placeholder command; replace with MCP + real sync commands in S1.1.
    run_sync = BashOperator(
        task_id="run_scaffold_sync",
        bash_command="python -m tbox_pipelines.cli sync",
    )

    run_sync
