from __future__ import annotations

from tbox_pipelines.config import load_config
from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.ragflow.client import RagflowClient


def run_sync(config_path: str | None = None) -> int:
    config = load_config(config_path)
    docs = fetch_stub_documents()
    client = RagflowClient(base_url=config.ragflow_base_url, api_key=config.ragflow_api_key)
    client.upload_documents(dataset_id=config.target_dataset_id, documents=docs)
    return len(docs)
