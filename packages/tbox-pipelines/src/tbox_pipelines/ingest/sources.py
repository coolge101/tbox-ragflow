from __future__ import annotations

import logging

import httpx

from tbox_pipelines.ingest.models import SourceDocument

logger = logging.getLogger(__name__)


def fetch_stub_documents() -> list[SourceDocument]:
    """Return deterministic fixtures for S1 scaffold tests."""
    return [
        SourceDocument(
            source_url="https://example.invalid/tbox/spec-overview",
            title="TBOX Spec Overview",
            content_markdown="# TBOX\n\nThis is a placeholder source document for S1.",
        )
    ]


def fetch_documents(
    *,
    provider: str = "stub",
    source_api_url: str = "",
    source_api_key: str = "",
    timeout_seconds: float = 15.0,
) -> list[SourceDocument]:
    if provider == "stub":
        return fetch_stub_documents()
    if provider == "http_json":
        return _fetch_http_json_documents(
            source_api_url=source_api_url,
            source_api_key=source_api_key,
            timeout_seconds=timeout_seconds,
        )
    raise ValueError(f"Unsupported source_provider={provider!r}")


def _fetch_http_json_documents(
    *,
    source_api_url: str,
    source_api_key: str,
    timeout_seconds: float,
) -> list[SourceDocument]:
    if not source_api_url:
        raise ValueError("source_api_url is required when source_provider=http_json")

    headers: dict[str, str] = {}
    if source_api_key:
        headers["Authorization"] = f"Bearer {source_api_key}"

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(source_api_url, headers=headers)
        response.raise_for_status()
        payload = response.json()

    docs_raw = payload.get("documents", []) if isinstance(payload, dict) else payload
    if not isinstance(docs_raw, list):
        raise ValueError("source_api response must contain a documents list")

    documents: list[SourceDocument] = []
    for idx, item in enumerate(docs_raw):
        if not isinstance(item, dict):
            logger.warning("skip_invalid_source_item index=%s type=%s", idx, type(item).__name__)
            continue
        source_url = str(item.get("source_url", "")).strip()
        title = str(item.get("title", "")).strip()
        content_markdown = str(item.get("content_markdown", "")).strip()
        if not source_url or not title or not content_markdown:
            logger.warning("skip_incomplete_source_item index=%s", idx)
            continue
        documents.append(
            SourceDocument(
                source_url=source_url,
                title=title,
                content_markdown=content_markdown,
                content_type=str(item.get("content_type", "text/markdown")),
            )
        )
    return documents
