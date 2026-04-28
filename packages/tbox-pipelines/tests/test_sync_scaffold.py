from tbox_pipelines.ingest.sources import fetch_stub_documents
from tbox_pipelines.workflows.sync_job import run_sync


def test_fetch_stub_documents_returns_one_item() -> None:
    docs = fetch_stub_documents()
    assert len(docs) == 1
    assert docs[0].title


def test_run_sync_without_dataset_id_returns_document_count() -> None:
    count = run_sync()
    assert count == 1
