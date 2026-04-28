from __future__ import annotations

import json

from tbox_pipelines.reporting import format_failure_summary, load_latest_sync_summary


def test_load_latest_sync_summary_filters_failed(tmp_path) -> None:
    audit_path = tmp_path / "sync_audit.jsonl"
    rows = [
        {"sync_id": "ok1", "status": "ok", "documents_fetched": 1},
        {"sync_id": "f1", "status": "failed", "reason": "dataset_not_resolved"},
        {"sync_id": "ok2", "status": "ok", "documents_fetched": 2},
        {"sync_id": "f2", "status": "failed", "reason": "remote_timeout"},
    ]
    audit_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    latest_failed = load_latest_sync_summary(str(audit_path), status="failed")
    assert latest_failed is not None
    assert latest_failed["sync_id"] == "f2"
    assert latest_failed["reason"] == "remote_timeout"


def test_format_failure_summary_contains_core_fields() -> None:
    message = format_failure_summary(
        {
            "sync_id": "abc123",
            "status": "failed",
            "reason": "dataset_not_resolved",
            "resolved_dataset_id": "",
            "documents_fetched": 5,
            "uploaded_doc_ids": ["d1", "d2"],
        }
    )
    assert "sync_failed" in message
    assert "sync_id=abc123" in message
    assert "reason=dataset_not_resolved" in message
    assert "documents_fetched=5" in message
    assert "uploaded_count=2" in message
