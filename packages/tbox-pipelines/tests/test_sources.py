from __future__ import annotations

from typing import Any

import pytest

from tbox_pipelines.ingest.sources import fetch_documents


class _DummyResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class _DummyClient:
    called_headers: dict[str, str] | None = None

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def get(self, _url: str, headers: dict[str, str]) -> _DummyResponse:
        _DummyClient.called_headers = headers
        return _DummyResponse(
            {
                "documents": [
                    {
                        "source_url": "https://example.invalid/a",
                        "title": "A",
                        "content_markdown": "# A",
                    },
                    {"source_url": "", "title": "bad", "content_markdown": "x"},
                ]
            }
        )


def test_fetch_documents_stub_provider() -> None:
    docs = fetch_documents(provider="stub")
    assert len(docs) == 1
    assert docs[0].title


def test_fetch_documents_http_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.ingest.sources.httpx.Client", _DummyClient)
    _DummyClient.called_headers = None
    docs = fetch_documents(
        provider="http_json",
        source_api_url="https://example.invalid/api/documents",
        source_api_key="token-demo",
    )
    assert len(docs) == 1
    assert docs[0].title == "A"
    assert _DummyClient.called_headers == {"Authorization": "Bearer token-demo"}


def test_fetch_documents_invalid_provider() -> None:
    with pytest.raises(ValueError):
        fetch_documents(provider="unknown")
