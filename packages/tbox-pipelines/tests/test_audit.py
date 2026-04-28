from __future__ import annotations

import json

from tbox_pipelines.audit import append_audit_record


def test_append_audit_record_creates_jsonl(tmp_path) -> None:
    log_path = tmp_path / "logs" / "sync_audit.jsonl"
    append_audit_record(str(log_path), {"status": "ok", "sync_id": "a"})
    append_audit_record(str(log_path), {"status": "failed", "sync_id": "b"})

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["status"] == "ok"
    assert second["status"] == "failed"
