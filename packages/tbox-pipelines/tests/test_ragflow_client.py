from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest

from tbox_pipelines.ingest.models import SourceDocument
from tbox_pipelines.ragflow.client import RagflowClient


class _DummyResponse:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self._payload = payload or {"data": []}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyClient:
    calls: list[dict] = []
    datasets_payload: list[dict[str, str]] = []

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def post(self, url: str, headers: dict, **kwargs: Any) -> _DummyResponse:
        _DummyClient.calls.append({"method": "POST", "url": url, "headers": headers, **kwargs})
        if url.endswith("/v1/document/upload"):
            return _DummyResponse(payload={"data": [{"id": "doc_1"}]})
        if url.endswith("/api/v1/datasets"):
            return _DummyResponse(payload={"data": {"id": "kb_new"}})
        return _DummyResponse()

    def get(self, url: str, headers: dict, **kwargs: Any) -> _DummyResponse:
        _DummyClient.calls.append({"method": "GET", "url": url, "headers": headers, **kwargs})
        if url.endswith("/api/v1/datasets"):
            return _DummyResponse(payload={"data": _DummyClient.datasets_payload})
        return _DummyResponse()


def test_upload_documents_uses_multipart_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    docs = [
        SourceDocument(
            source_url="https://example.invalid/a",
            title="TBOX Spec v1",
            content_markdown="# hello",
        )
    ]

    client = RagflowClient(base_url="http://localhost:9380", api_key="k")
    doc_ids = client.upload_documents(dataset_id="kb_demo", documents=docs)

    assert doc_ids == ["doc_1"]
    assert len(_DummyClient.calls) == 1
    call = _DummyClient.calls[0]
    assert call["url"] == "http://localhost:9380/v1/document/upload"
    assert call["headers"]["Authorization"] == "Bearer k"
    assert call["data"] == {"kb_id": "kb_demo"}
    file_entry = call["files"]["file"]
    assert file_entry[0].endswith(".md")
    assert isinstance(file_entry[1], BytesIO)


def test_upload_documents_skip_when_dataset_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    client = RagflowClient(base_url="http://localhost:9380")
    doc_ids = client.upload_documents(dataset_id="", documents=[])

    assert doc_ids == []
    assert _DummyClient.calls == []


def test_run_documents_calls_run_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    client = RagflowClient(base_url="http://localhost:9380", api_key="k")
    client.run_documents(["doc_a", "doc_b"])

    assert len(_DummyClient.calls) == 1
    call = _DummyClient.calls[0]
    assert call["url"] == "http://localhost:9380/v1/document/run"
    assert call["json"] == {"doc_ids": ["doc_a", "doc_b"], "run": "1"}
    assert call["headers"]["Authorization"] == "Bearer k"


def test_run_documents_skip_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    client = RagflowClient(base_url="http://localhost:9380")
    client.run_documents([])

    assert _DummyClient.calls == []


def test_resolve_dataset_id_prefers_explicit_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    client = RagflowClient(base_url="http://localhost:9380")
    dataset_id = client.resolve_dataset_id(dataset_id="kb_fixed", dataset_name="ignored")

    assert dataset_id == "kb_fixed"
    assert _DummyClient.calls == []


def test_resolve_dataset_id_uses_existing_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []
    _DummyClient.datasets_payload = [{"id": "kb_existing", "name": "TBOX-KB"}]

    client = RagflowClient(base_url="http://localhost:9380")
    dataset_id = client.resolve_dataset_id(dataset_id="", dataset_name="TBOX-KB")

    assert dataset_id == "kb_existing"
    assert len(_DummyClient.calls) == 1
    assert _DummyClient.calls[0]["method"] == "GET"


def test_resolve_dataset_id_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ragflow.client.httpx.Client", _DummyClient)
    _DummyClient.calls = []
    _DummyClient.datasets_payload = []

    client = RagflowClient(base_url="http://localhost:9380")
    dataset_id = client.resolve_dataset_id(dataset_id="", dataset_name="TBOX-KB", auto_create=True)

    assert dataset_id == "kb_new"
    assert len(_DummyClient.calls) == 2
    assert _DummyClient.calls[0]["method"] == "GET"
    assert _DummyClient.calls[1]["method"] == "POST"
    assert _DummyClient.calls[1]["json"] == {"name": "TBOX-KB"}
