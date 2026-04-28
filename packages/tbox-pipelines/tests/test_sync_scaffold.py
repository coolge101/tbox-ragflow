import json

from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.workflows.sync_job import run_sync


class _DummyClient:
    upload_called = False
    run_called = False
    resolve_called = False

    def __init__(self, *args, **kwargs) -> None:
        pass

    def resolve_dataset_id(
        self,
        dataset_id: str,
        dataset_name: str,
        auto_create: bool = True,
    ) -> str:
        _DummyClient.resolve_called = True
        return dataset_id or "kb_auto"

    def upload_documents(self, dataset_id: str, documents: list, sync_id: str = "") -> list[str]:
        _DummyClient.upload_called = True
        return ["doc_1"]

    def run_documents(self, doc_ids: list[str], sync_id: str = "") -> None:
        _DummyClient.run_called = True


def test_fetch_stub_documents_returns_one_item() -> None:
    docs = fetch_stub_documents()
    assert len(docs) == 1
    assert docs[0].title


def test_run_sync_raises_when_dataset_not_resolved(tmp_path) -> None:
    cfg = {
        "ragflow_base_url": "http://localhost:9380",
        "ragflow_api_key": "",
        "target_dataset_id": "",
        "target_dataset_name": "",
        "auto_create_dataset": False,
        "auto_run_after_upload": True,
        "http_max_retries": 0,
        "http_retry_backoff_seconds": 0.0,
    }
    cfg_path = tmp_path / "pipeline.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    import pytest

    from tbox_pipelines.workflows.sync_job import SyncConfigError

    with pytest.raises(SyncConfigError):
        run_sync(str(cfg_path))


def test_run_sync_triggers_run_when_enabled(monkeypatch) -> None:
    _DummyClient.resolve_called = False
    _DummyClient.upload_called = False
    _DummyClient.run_called = False

    monkeypatch.setattr("tbox_pipelines.workflows.sync_job.RagflowClient", _DummyClient)
    monkeypatch.setenv("RAGFLOW_DATASET_ID", "kb_demo")
    monkeypatch.setenv("RAGFLOW_AUTO_RUN", "true")

    count = run_sync()

    assert count == 1
    assert _DummyClient.resolve_called
    assert _DummyClient.upload_called
    assert _DummyClient.run_called


def test_run_sync_denied_for_viewer_role(monkeypatch) -> None:
    monkeypatch.setenv("TBOX_ACTOR_ROLE", "viewer")
    monkeypatch.setenv("RAGFLOW_AUTO_CREATE_DATASET", "false")
    monkeypatch.setenv("RAGFLOW_AUTO_RUN", "false")

    import pytest

    from tbox_pipelines.workflows.sync_job import SyncConfigError

    with pytest.raises(SyncConfigError):
        run_sync()


def test_run_sync_invalid_rbac_policy_path(monkeypatch) -> None:
    monkeypatch.setenv("TBOX_RBAC_POLICY_PATH", "/tmp/path/does/not/exist.json")
    monkeypatch.setenv("RAGFLOW_AUTO_CREATE_DATASET", "false")
    monkeypatch.setenv("RAGFLOW_AUTO_RUN", "false")

    import pytest

    from tbox_pipelines.workflows.sync_job import SyncConfigError

    with pytest.raises(SyncConfigError):
        run_sync()


def test_run_sync_writes_rbac_audit_log(tmp_path) -> None:
    cfg = {
        "ragflow_base_url": "http://localhost:9380",
        "ragflow_api_key": "",
        "target_dataset_id": "",
        "target_dataset_name": "",
        "auto_create_dataset": False,
        "auto_run_after_upload": False,
        "http_max_retries": 0,
        "http_retry_backoff_seconds": 0.0,
        "audit_log_path": str(tmp_path / "sync_audit.jsonl"),
        "rbac_audit_log_path": str(tmp_path / "rbac_audit.jsonl"),
        "actor_role": "viewer",
    }
    cfg_path = tmp_path / "pipeline.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    import pytest

    from tbox_pipelines.workflows.sync_job import SyncConfigError

    with pytest.raises(SyncConfigError):
        run_sync(str(cfg_path))

    records = (tmp_path / "rbac_audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(records) >= 1
    last = json.loads(records[-1])
    assert last["reason"] == "permission_denied"
    assert last["actor_role"] == "viewer"


def test_run_sync_notifies_rbac_high_risk_event(monkeypatch) -> None:
    calls: list[dict] = []

    def _fake_notify(_url: str, summary: dict, timeout_seconds: float = 10.0) -> bool:
        _ = timeout_seconds
        calls.append(summary)
        return True

    monkeypatch.setattr("tbox_pipelines.workflows.sync_job.send_webhook_notification", _fake_notify)
    monkeypatch.setenv("TBOX_ACTOR_ROLE", "viewer")
    monkeypatch.setenv("RAGFLOW_AUTO_CREATE_DATASET", "false")
    monkeypatch.setenv("RAGFLOW_AUTO_RUN", "false")
    monkeypatch.setenv("TBOX_RBAC_ALERT_WEBHOOK_URL", "http://example.invalid/rbac")
    monkeypatch.setenv("TBOX_RBAC_ALERT_HIGH_RISK_REASONS", "permission_denied")
    monkeypatch.setenv("RAGFLOW_NOTIFY_WEBHOOK_URL", "")

    import pytest

    from tbox_pipelines.workflows.sync_job import SyncConfigError

    with pytest.raises(SyncConfigError):
        run_sync()

    assert len(calls) >= 1
    rbac_calls = [payload for payload in calls if "documents_fetched" not in payload]
    assert len(rbac_calls) == 1
    assert rbac_calls[0]["reason"] == "permission_denied"
