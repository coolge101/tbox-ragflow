from __future__ import annotations

from tbox_pipelines.config import load_config
from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.ragflow.client import RagflowClient


def run_sync(config_path: str | None = None) -> int:
    config = load_config(config_path)
    docs = fetch_stub_documents()
    client = RagflowClient(base_url=config.ragflow_base_url, api_key=config.ragflow_api_key)

    resolved_dataset_id = client.resolve_dataset_id(
        dataset_id=config.target_dataset_id,
        dataset_name=config.target_dataset_name,
        auto_create=config.auto_create_dataset,
    )
    doc_ids = client.upload_documents(dataset_id=resolved_dataset_id, documents=docs)
    if config.auto_run_after_upload:
        client.run_documents(doc_ids)
    return len(docs)
