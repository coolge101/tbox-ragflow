from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from tbox_pipelines.audit import append_audit_record
from tbox_pipelines.config import load_config
from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.ragflow.client import RagflowClient

logger = logging.getLogger(__name__)


class SyncConfigError(ValueError):
    """Raised when required sync configuration is missing or invalid."""


def _emit_sync_summary(summary: dict[str, Any], audit_log_path: str) -> None:
    logger.info("sync_summary %s", json.dumps(summary, ensure_ascii=False))
    append_audit_record(audit_log_path, summary)


def run_sync(config_path: str | None = None) -> int:
    sync_id = uuid.uuid4().hex
    config = load_config(config_path)
    docs = fetch_stub_documents()
    client = RagflowClient(
        base_url=config.ragflow_base_url,
        api_key=config.ragflow_api_key,
        max_retries=config.http_max_retries,
        retry_backoff_seconds=config.http_retry_backoff_seconds,
    )

    resolved_dataset_id = client.resolve_dataset_id(
        dataset_id=config.target_dataset_id,
        dataset_name=config.target_dataset_name,
        auto_create=config.auto_create_dataset,
    )
    if not resolved_dataset_id:
        summary = {
            "sync_id": sync_id,
            "documents_fetched": len(docs),
            "resolved_dataset_id": "",
            "uploaded_doc_ids": [],
            "run_triggered": False,
            "auto_run_after_upload": config.auto_run_after_upload,
            "status": "failed",
            "reason": "dataset_not_resolved",
        }
        _emit_sync_summary(summary, config.audit_log_path)
        raise SyncConfigError(
            "Unable to resolve target dataset id. Set RAGFLOW_DATASET_ID or RAGFLOW_DATASET_NAME."
        )

    doc_ids = client.upload_documents(
        dataset_id=resolved_dataset_id,
        documents=docs,
        sync_id=sync_id,
    )

    run_triggered = False
    if config.auto_run_after_upload:
        client.run_documents(doc_ids, sync_id=sync_id)
        run_triggered = bool(doc_ids)

    summary = {
        "sync_id": sync_id,
        "documents_fetched": len(docs),
        "resolved_dataset_id": resolved_dataset_id,
        "uploaded_doc_ids": doc_ids,
        "run_triggered": run_triggered,
        "auto_run_after_upload": config.auto_run_after_upload,
        "status": "ok",
    }
    _emit_sync_summary(summary, config.audit_log_path)
    return len(docs)
