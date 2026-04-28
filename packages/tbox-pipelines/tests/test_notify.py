from __future__ import annotations

from typing import Any

import pytest

from tbox_pipelines.notify import send_webhook_notification, should_notify


class _DummyResponse:
    def raise_for_status(self) -> None:
        return None


class _DummyClient:
    calls: list[dict[str, Any]] = []

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
        _DummyClient.calls.append({"url": url, "headers": headers, "json": json})
        return _DummyResponse()


def test_should_notify_default_failed_only() -> None:
    assert should_notify({"status": "failed"}, notify_on_success=False)
    assert not should_notify({"status": "ok"}, notify_on_success=False)


def test_send_webhook_notification_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "abc"},
    )
    assert ok
    assert len(_DummyClient.calls) == 1
    call = _DummyClient.calls[0]
    assert call["json"]["type"] == "tbox_sync_summary"
