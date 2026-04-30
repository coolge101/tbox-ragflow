from __future__ import annotations

import importlib.metadata
from typing import Any

import httpx
import pytest

from tbox_pipelines.notify import (
    WEBHOOK_PAYLOAD_VERSION,
    WEBHOOK_TYPE_TBOX_RBAC_ALERT,
    WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
    build_tbox_rbac_alert_payload,
    build_tbox_sync_summary_payload,
    send_rbac_webhook_notification,
    send_webhook_notification,
    should_notify,
    should_notify_rbac_event,
)


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


def test_webhook_user_agent_fallback_when_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr("tbox_pipelines.notify.importlib.metadata.version", _raise)
    import tbox_pipelines.notify as notify_mod

    assert notify_mod._webhook_post_headers()["User-Agent"] == "tbox-pipelines"


def test_send_webhook_omits_sync_header_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []
    assert send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": ""},
    )
    assert "X-TBOX-Sync-Id" not in _DummyClient.calls[0]["headers"]


def test_send_webhook_retries_transient_connect_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.time.sleep", lambda _s: None)

    class _Flaky:
        n = 0

        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_Flaky":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            _Flaky.n += 1
            if _Flaky.n < 3:
                raise httpx.ConnectError("simulated", request=httpx.Request("POST", url))
            return _DummyResponse()

    _Flaky.n = 0
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _Flaky)
    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "z"},
        max_retries=3,
        retry_backoff_seconds=0.01,
    )
    assert ok
    assert _Flaky.n == 3


def test_send_webhook_no_retry_on_non_transient_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.time.sleep", lambda _s: None)

    class _Client403:
        n = 0

        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_Client403":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            _Client403.n += 1
            req = httpx.Request("POST", url)
            resp = httpx.Response(403, request=req)
            raise httpx.HTTPStatusError("forbidden", request=req, response=resp)

    _Client403.n = 0
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _Client403)
    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "x"},
        max_retries=3,
        retry_backoff_seconds=0.01,
    )
    assert not ok
    assert _Client403.n == 1


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
    assert call["headers"]["Content-Type"] == "application/json"
    assert call["headers"]["User-Agent"].startswith("tbox-pipelines/")
    assert call["json"]["payload_version"] == WEBHOOK_PAYLOAD_VERSION
    assert call["json"]["type"] == WEBHOOK_TYPE_TBOX_SYNC_SUMMARY


def test_send_rbac_webhook_notification_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_rbac_webhook_notification(
        "http://example.invalid/rbac-hook",
        {
            "sync_id": "s1",
            "status": "failed",
            "reason": "permission_denied",
            "actor_role": "viewer",
            "rbac_alert_suppressed_in_window": 2,
        },
    )
    assert ok
    assert len(_DummyClient.calls) == 1
    assert _DummyClient.calls[0]["headers"]["User-Agent"].startswith("tbox-pipelines/")
    assert _DummyClient.calls[0]["headers"]["X-TBOX-Sync-Id"] == "s1"
    body = _DummyClient.calls[0]["json"]
    assert body["payload_version"] == WEBHOOK_PAYLOAD_VERSION
    assert body["type"] == WEBHOOK_TYPE_TBOX_RBAC_ALERT
    assert body["sync_id"] == "s1"
    assert body["status"] == "failed"
    assert body["rbac"]["reason"] == "permission_denied"
    assert body["rbac"]["rbac_alert_suppressed_in_window"] == 2


def test_build_payloads_match_send_helpers() -> None:
    summary = {"status": "failed", "sync_id": "z"}
    assert build_tbox_sync_summary_payload(summary) == {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        "status": "failed",
        "sync_id": "z",
        "summary": summary,
    }
    ev = {"sync_id": "s", "status": "failed", "reason": "x"}
    assert build_tbox_rbac_alert_payload(ev) == {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": WEBHOOK_TYPE_TBOX_RBAC_ALERT,
        "status": "failed",
        "sync_id": "s",
        "rbac": ev,
    }


def test_should_notify_rbac_event_high_risk() -> None:
    assert should_notify_rbac_event(
        {"status": "failed", "reason": "permission_denied"},
        ("permission_denied",),
    )
    assert not should_notify_rbac_event(
        {"status": "ok", "reason": "policy_loaded"},
        ("permission_denied",),
    )
