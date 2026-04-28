from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_latest_sync_summary(path: str, status: str | None = None) -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return None

    lines = target.read_text(encoding="utf-8").splitlines()
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if status and payload.get("status") != status:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def format_failure_summary(summary: dict[str, Any]) -> str:
    sync_id = str(summary.get("sync_id", ""))
    reason = str(summary.get("reason", "unknown"))
    dataset_id = str(summary.get("resolved_dataset_id", ""))
    docs_fetched = summary.get("documents_fetched", 0)
    uploaded_doc_ids = summary.get("uploaded_doc_ids", [])

    return (
        "sync_failed "
        f"sync_id={sync_id} "
        f"reason={reason} "
        f"resolved_dataset_id={dataset_id} "
        f"documents_fetched={docs_fetched} "
        f"uploaded_count={len(uploaded_doc_ids) if isinstance(uploaded_doc_ids, list) else 0}"
    )
