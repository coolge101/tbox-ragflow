from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

import httpx

from tbox_pipelines.ingest.models import SourceDocument

logger = logging.getLogger(__name__)


class RagflowClient:
    def __init__(self, base_url: str, api_key: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def upload_documents(self, dataset_id: str, documents: list[SourceDocument]) -> list[str]:
        if not dataset_id:
            logger.warning("RAGFLOW_DATASET_ID is empty; skip upload in scaffold mode")
            return []

        headers = self._build_headers()
        url = f"{self._base_url}/v1/document/upload"
        doc_ids: list[str] = []
        for idx, doc in enumerate(documents, start=1):
            filename = self._build_filename(doc, idx)
            file_content = doc.content_markdown.encode("utf-8")
            file_tuple = (filename, BytesIO(file_content), "text/markdown")

            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    url,
                    headers=headers,
                    data={"kb_id": dataset_id},
                    files={"file": file_tuple},
                )
                response.raise_for_status()
                doc_ids.extend(self._extract_doc_ids(response))

        return doc_ids

    def run_documents(self, doc_ids: list[str]) -> None:
        if not doc_ids:
            return

        url = f"{self._base_url}/v1/document/run"
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"

        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=headers, json={"doc_ids": doc_ids, "run": "1"})
            response.raise_for_status()

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @staticmethod
    def _build_filename(document: SourceDocument, index: int) -> str:
        stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in document.title)
        stem = stem.strip("_") or f"doc_{index}"
        return f"{stem}.md"

    @staticmethod
    def _extract_doc_ids(response: httpx.Response) -> list[str]:
        try:
            payload: Any = response.json()
        except Exception:
            return []

        raw_data = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(raw_data, list):
            return []

        ids: list[str] = []
        for item in raw_data:
            if isinstance(item, dict):
                doc_id = item.get("id")
                if isinstance(doc_id, str) and doc_id:
                    ids.append(doc_id)
            elif isinstance(item, str) and item:
                ids.append(item)
        return ids
