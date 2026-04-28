from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    source_url: str
    title: str
    content_markdown: str
    content_type: str = "text/markdown"
