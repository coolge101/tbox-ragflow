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

    def upload_documents(self, dataset_id: str, documents: list) -> list[str]:
        _DummyClient.upload_called = True
        return ["doc_1"]

    def run_documents(self, doc_ids: list[str]) -> None:
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
