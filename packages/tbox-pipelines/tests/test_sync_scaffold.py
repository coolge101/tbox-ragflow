from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.workflows.sync_job import run_sync


class _DummyClient:
    upload_called = False
    run_called = False

    def __init__(self, *args, **kwargs) -> None:
        pass

    def upload_documents(self, dataset_id: str, documents: list) -> list[str]:
        _DummyClient.upload_called = True
        return ["doc_1"]

    def run_documents(self, doc_ids: list[str]) -> None:
        _DummyClient.run_called = True


def test_fetch_stub_documents_returns_one_item() -> None:
    docs = fetch_stub_documents()
    assert len(docs) == 1
    assert docs[0].title


def test_run_sync_without_dataset_id_returns_document_count() -> None:
    count = run_sync()
    assert count == 1


def test_run_sync_triggers_run_when_enabled(monkeypatch) -> None:
    _DummyClient.upload_called = False
    _DummyClient.run_called = False

    monkeypatch.setattr("tbox_pipelines.workflows.sync_job.RagflowClient", _DummyClient)
    monkeypatch.setenv("RAGFLOW_DATASET_ID", "kb_demo")
    monkeypatch.setenv("RAGFLOW_AUTO_RUN", "true")

    count = run_sync()

    assert count == 1
    assert _DummyClient.upload_called
    assert _DummyClient.run_called
