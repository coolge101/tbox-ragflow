from __future__ import annotations

from io import BytesIO

import pytest

from tbox_pipelines.ingest.models import SourceDocument
from tbox_pipelines.ragflow.client import RagflowClient


class _DummyResponse:
    def raise_for_status(self) -> None:
        return None


class _DummyClient:
    calls: list[dict] = []

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def post(self, url: str, headers: dict, data: dict, files: dict) -> _DummyResponse:
        _DummyClient.calls.append({"url": url, "headers": headers, "data": data, "files": files})
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
    client.upload_documents(dataset_id="kb_demo", documents=docs)

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
    client.upload_documents(dataset_id="", documents=[])

    assert _DummyClient.calls == []
