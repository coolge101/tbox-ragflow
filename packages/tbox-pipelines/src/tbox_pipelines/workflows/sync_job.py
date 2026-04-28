from __future__ import annotations

import json
import logging

from tbox_pipelines.config import load_config
from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.ragflow.client import RagflowClient

logger = logging.getLogger(__name__)


def run_sync(config_path: str | None = None) -> int:
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
    doc_ids = client.upload_documents(dataset_id=resolved_dataset_id, documents=docs)

    run_triggered = False
    if config.auto_run_after_upload:
        client.run_documents(doc_ids)
        run_triggered = bool(doc_ids)

    logger.info(
        "sync_summary %s",
        json.dumps(
            {
                "documents_fetched": len(docs),
                "resolved_dataset_id": resolved_dataset_id,
                "uploaded_doc_ids": doc_ids,
                "run_triggered": run_triggered,
                "auto_run_after_upload": config.auto_run_after_upload,
            },
            ensure_ascii=False,
        ),
    )
    return len(docs)
