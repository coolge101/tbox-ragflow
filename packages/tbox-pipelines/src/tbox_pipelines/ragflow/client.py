from __future__ import annotations

import logging
from io import BytesIO

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

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        url = f"{self._base_url}/v1/document/upload"
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

    @staticmethod
    def _build_filename(document: SourceDocument, index: int) -> str:
        stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in document.title)
        stem = stem.strip("_") or f"doc_{index}"
        return f"{stem}.md"
