from __future__ import annotations

from tbox_pipelines.ingest.models import SourceDocument


def fetch_stub_documents() -> list[SourceDocument]:
    """Return deterministic fixtures for S1 scaffold tests."""
    return [
        SourceDocument(
            source_url="https://example.invalid/tbox/spec-overview",
            title="TBOX Spec Overview",
            content_markdown="# TBOX\n\nThis is a placeholder source document for S1.",
        )
    ]
