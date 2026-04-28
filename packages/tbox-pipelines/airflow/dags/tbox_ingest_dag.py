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
    # S1.5: support dag_run.conf to override dataset/retry knobs per run.
    run_sync = BashOperator(
        task_id="run_scaffold_sync",
        env={
            "RAGFLOW_DATASET_ID": "{{ dag_run.conf.get('dataset_id', '') if dag_run else '' }}",
            "RAGFLOW_DATASET_NAME": "{{ dag_run.conf.get('dataset_name', 'TBOX-KB-DEFAULT') if dag_run else 'TBOX-KB-DEFAULT' }}",
            "RAGFLOW_AUTO_CREATE_DATASET": "{{ dag_run.conf.get('auto_create_dataset', 'true') if dag_run else 'true' }}",
            "RAGFLOW_AUTO_RUN": "{{ dag_run.conf.get('auto_run', 'true') if dag_run else 'true' }}",
            "RAGFLOW_HTTP_MAX_RETRIES": "{{ dag_run.conf.get('http_max_retries', '2') if dag_run else '2' }}",
            "RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS": "{{ dag_run.conf.get('http_retry_backoff_seconds', '1.0') if dag_run else '1.0' }}",
        },
        bash_command="python -m tbox_pipelines.cli sync --config config/pipeline.sample.json",
    )

    run_sync
