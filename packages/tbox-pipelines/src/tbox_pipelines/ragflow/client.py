from __future__ import annotations

import logging
from dataclasses import asdict

import httpx

from tbox_pipelines.ingest.models import SourceDocument

logger = logging.getLogger(__name__)


class RagflowClient:
    def __init__(self, base_url: str, api_key: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def upload_documents(self, dataset_id: str, documents: list[SourceDocument]) -> None:
        if not dataset_id:
            logger.warning("RAGFLOW_DATASET_ID is empty; skip upload in scaffold mode")
            return

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "dataset_id": dataset_id,
            "documents": [asdict(doc) for doc in documents],
        }
        # Placeholder endpoint for S1 scaffold; replace with real API in S1.1.
        url = f"{self._base_url}/api/v1/tbox/scaffold-upload"
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
