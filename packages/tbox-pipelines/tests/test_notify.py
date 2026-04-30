from __future__ import annotations

import importlib.metadata
import logging
from datetime import date
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
    status_code = 200

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


def _assert_log_contains_fields(message: str, fields: tuple[str, ...]) -> None:
    for field in fields:
        assert f"{field}=" in message


def test_webhook_user_agent_fallback_when_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr("tbox_pipelines.notify.importlib.metadata.version", _raise)
    import tbox_pipelines.notify as notify_mod

    assert notify_mod._webhook_post_headers()["User-Agent"] == "tbox-pipelines"


def test_webhook_notify_failed_log_uses_redacted_url(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)

    class _FailClient:
        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_FailClient":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            raise httpx.ConnectError("simulated", request=httpx.Request("POST", url))

    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _FailClient)
    ok = send_webhook_notification(
        "https://user:pass@host.invalid/hook?token=SECRET&x=1#frag",
        {"status": "failed", "sync_id": "s1"},
    )
    assert not ok
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "outcome=failure" in joined
    assert "log_schema_version=1" in joined
    assert "delivery_state=failed" in joined
    assert "payload_type=tbox_sync_summary" in joined
    assert "sync_id=s1" in joined
    assert "attempt_elapsed_ms=" in joined
    assert "total_elapsed_ms=" in joined
    assert "https://***@host.invalid/hook" in joined
    assert "SECRET" not in joined


def test_webhook_http_url_allowed_only_http_https_with_host() -> None:
    import tbox_pipelines.notify as notify_mod

    assert notify_mod._webhook_http_url_allowed("http://example.com/h")
    assert notify_mod._webhook_http_url_allowed("https://x.example/hook")
    assert not notify_mod._webhook_http_url_allowed("file:///etc/passwd")
    assert not notify_mod._webhook_http_url_allowed("relative/path")
    assert not notify_mod._webhook_http_url_allowed("ftp://example.com/x")


def test_send_webhook_skips_invalid_url_scheme(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_webhook_notification(
        "file:///tmp/x",
        {"status": "failed", "sync_id": "a"},
    )
    assert not ok
    assert _DummyClient.calls == []
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "webhook_notify_skipped_invalid_url" in joined
    assert "log_schema_version=1" in joined
    assert "payload_type=tbox_sync_summary" in joined
    assert "sync_id=a" in joined
    assert "skip_reason=invalid_url" in joined
    assert "url=file:///tmp/x" in joined


def test_send_rbac_webhook_skips_invalid_url_with_context(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_rbac_webhook_notification(
        "file:///tmp/rbac",
        {"status": "failed", "sync_id": "rb1", "reason": "permission_denied"},
    )
    assert not ok
    assert _DummyClient.calls == []
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "webhook_notify_skipped_invalid_url" in joined
    assert "log_schema_version=1" in joined
    assert "payload_type=tbox_rbac_alert" in joined
    assert "sync_id=rb1" in joined
    assert "skip_reason=invalid_url" in joined
    assert "url=file:///tmp/rbac" in joined


def test_webhook_url_for_logs_strips_query_fragment_and_masks_userinfo() -> None:
    import tbox_pipelines.notify as notify_mod

    assert (
        notify_mod._webhook_url_for_logs("https://u:p@example.com/hook?token=secret#x")
        == "https://***@example.com/hook"
    )
    assert notify_mod._webhook_url_for_logs("http://example.com/cb?k=v") == "http://example.com/cb"


def test_webhook_idempotency_key_deterministic() -> None:
    import tbox_pipelines.notify as notify_mod

    a = notify_mod._webhook_idempotency_key(
        notify_mod.WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        {"sync_id": "1", "status": "ok"},
    )
    b = notify_mod._webhook_idempotency_key(
        notify_mod.WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        {"status": "ok", "sync_id": "1"},
    )
    assert a == b
    assert len(a) == 64
    c = notify_mod._webhook_idempotency_key(
        notify_mod.WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        {"sync_id": "1", "status": "failed"},
    )
    assert c != a


def test_webhook_idempotency_key_non_json_values_use_default_str() -> None:
    import tbox_pipelines.notify as notify_mod

    k = notify_mod._webhook_idempotency_key(
        notify_mod.WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        {"d": date(2026, 4, 30)},
    )
    assert len(k) == 64


@pytest.mark.parametrize(
    (
        "status_code",
        "retry_after",
        "backoff",
        "expected_policy",
        "expected_retry_in",
        "expected_source",
    ),
    [
        (429, "3", 0.1, "retry_after", 3.0, "header"),
        (429, None, 0.2, "backoff", 0.2, None),
        (429, "soon", 0.2, "backoff", 0.2, None),
    ],
)
def test_webhook_retry_decision_http_status_cases(
    status_code: int,
    retry_after: str | None,
    backoff: float,
    expected_policy: str,
    expected_retry_in: float,
    expected_source: str | None,
) -> None:
    import tbox_pipelines.notify as notify_mod

    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    req = httpx.Request("POST", "http://example.invalid/webhook")
    resp = httpx.Response(status_code, request=req, headers=headers)
    exc = httpx.HTTPStatusError("boom", request=req, response=resp)
    d = notify_mod._webhook_retry_decision(exc=exc, attempt=1, attempts=2, backoff=backoff)
    assert d.will_retry
    assert not d.is_final
    assert d.delivery_state == "retrying"
    assert d.retry_policy == expected_policy
    assert d.retry_in_seconds == expected_retry_in
    assert d.retry_after_source == expected_source
    assert d.retry_window_ms == int(expected_retry_in * 1000)


def test_webhook_retry_decision_non_retryable_http_final() -> None:
    import tbox_pipelines.notify as notify_mod

    req = httpx.Request("POST", "http://example.invalid/webhook")
    resp = httpx.Response(403, request=req)
    exc = httpx.HTTPStatusError("forbidden", request=req, response=resp)
    d = notify_mod._webhook_retry_decision(exc=exc, attempt=1, attempts=3, backoff=0.5)
    assert not d.will_retry
    assert d.is_final
    assert d.delivery_state == "failed"
    assert d.retry_policy == "none"
    assert d.retry_eligible is False
    assert d.retries_remaining == 2
    assert d.retry_in_seconds is None
    assert d.retry_window_ms is None


def test_send_webhook_omits_sync_header_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []
    assert send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": ""},
    )
    hdrs = _DummyClient.calls[0]["headers"]
    assert "X-TBOX-Sync-Id" not in hdrs
    assert len(hdrs["Idempotency-Key"]) == 64


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
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
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
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "outcome=failure" in joined
    assert "log_schema_version=1" in joined
    assert "delivery_state=failed" in joined
    assert "final=True" in joined
    assert "retry=False" in joined
    assert "retry_reason=http_non_retryable_403" in joined


def test_send_webhook_retry_honors_retry_after_header(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
    slept: list[float] = []
    monkeypatch.setattr("tbox_pipelines.notify.time.sleep", lambda s: slept.append(float(s)))

    class _Client429:
        n = 0

        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_Client429":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            _Client429.n += 1
            if _Client429.n == 1:
                req = httpx.Request("POST", url)
                resp = httpx.Response(429, request=req, headers={"Retry-After": "3"})
                raise httpx.HTTPStatusError("rate limited", request=req, response=resp)
            return _DummyResponse()

    _Client429.n = 0
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _Client429)
    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "ra1"},
        max_retries=1,
        retry_backoff_seconds=0.1,
    )
    assert ok
    assert _Client429.n == 2
    assert slept == [3.0]
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "outcome=failure" in joined
    assert "log_schema_version=1" in joined
    assert "delivery_state=retrying" in joined
    assert "final=False" in joined
    assert "retry_policy=retry_after" in joined
    assert "retry_eligible=True" in joined
    assert "retries_remaining=1" in joined
    assert "http_status=429" in joined
    assert "retry_after_seconds=3.0" in joined
    assert "retry_after_source=header" in joined
    assert "backoff_seconds=0.1" in joined
    assert "retry_in_seconds=3.0" in joined
    assert "retry_window_ms=3000" in joined
    assert "retry_reason=http_429" in joined
    assert "error_class=HTTPStatusError" in joined
    assert "error_family=http" in joined


def test_send_webhook_retry_after_invalid_falls_back_to_backoff(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
    slept: list[float] = []
    monkeypatch.setattr("tbox_pipelines.notify.time.sleep", lambda s: slept.append(float(s)))

    class _Client429Invalid:
        n = 0

        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_Client429Invalid":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            _Client429Invalid.n += 1
            if _Client429Invalid.n == 1:
                req = httpx.Request("POST", url)
                resp = httpx.Response(429, request=req, headers={"Retry-After": "soon"})
                raise httpx.HTTPStatusError("rate limited", request=req, response=resp)
            return _DummyResponse()

    _Client429Invalid.n = 0
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _Client429Invalid)
    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "ra2"},
        max_retries=1,
        retry_backoff_seconds=0.2,
    )
    assert ok
    assert _Client429Invalid.n == 2
    assert slept == [0.2]
    joined = " | ".join(r.getMessage() for r in caplog.records)
    assert "outcome=failure" in joined
    assert "log_schema_version=1" in joined
    assert "delivery_state=retrying" in joined
    assert "final=False" in joined
    assert "retry_policy=backoff" in joined
    assert "retry_eligible=True" in joined
    assert "retries_remaining=1" in joined
    assert "http_status=429" in joined
    assert "retry_after_seconds=None" in joined
    assert "retry_after_source=None" in joined
    assert "backoff_seconds=0.2" in joined
    assert "retry_in_seconds=0.2" in joined
    assert "retry_window_ms=200" in joined
    assert "retry_reason=http_429" in joined
    assert "error_class=HTTPStatusError" in joined
    assert "error_family=http" in joined


def test_send_webhook_retry_after_http_date_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slept: list[float] = []
    monkeypatch.setattr("tbox_pipelines.notify.time.sleep", lambda s: slept.append(float(s)))
    monkeypatch.setattr("tbox_pipelines.notify.time.time", lambda: 1000.0)

    class _Client429Date:
        n = 0

        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_Client429Date":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            _Client429Date.n += 1
            if _Client429Date.n == 1:
                req = httpx.Request("POST", url)
                # 1005s epoch => 5 seconds after mocked now.
                resp = httpx.Response(
                    429,
                    request=req,
                    headers={"Retry-After": "Thu, 01 Jan 1970 00:16:45 GMT"},
                )
                raise httpx.HTTPStatusError("rate limited", request=req, response=resp)
            return _DummyResponse()

    _Client429Date.n = 0
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _Client429Date)
    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "ra3"},
        max_retries=1,
        retry_backoff_seconds=0.1,
    )
    assert ok
    assert _Client429Date.n == 2
    assert slept == [5.0]


def test_should_notify_default_failed_only() -> None:
    assert should_notify({"status": "failed"}, notify_on_success=False)
    assert not should_notify({"status": "ok"}, notify_on_success=False)


def test_send_webhook_notification_logs_ok_at_debug(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_webhook_notification(
        "https://hooks.example.invalid/webhook?token=x",
        {"status": "failed", "sync_id": "abc"},
    )
    assert ok
    msgs = [r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("webhook_notify_ok" in m and "http_status=200" in m for m in msgs)
    assert any("log_schema_version=1" in m for m in msgs)
    assert any("outcome=success" in m for m in msgs)
    assert any("delivery_state=delivered" in m for m in msgs)
    assert any("payload_type=tbox_sync_summary" in m for m in msgs)
    assert any("sync_id=abc" in m for m in msgs)
    assert any("attempt_elapsed_ms=" in m and "total_elapsed_ms=" in m for m in msgs)
    assert any("https://hooks.example.invalid/webhook" in m and "token=" not in m for m in msgs)


def test_webhook_log_context_fields_consistent_across_paths(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.DEBUG)

    # success path
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []
    assert send_webhook_notification(
        "http://example.invalid/ok",
        {"status": "failed", "sync_id": "ctx1"},
    )
    success_msg = next(
        r.getMessage() for r in caplog.records if "webhook_notify_ok" in r.getMessage()
    )
    _assert_log_contains_fields(
        success_msg,
        (
            "log_schema_version",
            "outcome",
            "payload_type",
            "sync_id",
            "url",
            "attempt",
            "delivery_state",
            "attempt_index",
            "attempt_total",
            "http_status",
            "attempt_elapsed_ms",
            "total_elapsed_ms",
        ),
    )

    # failure path
    class _AlwaysFailClient:
        def __init__(self, *_a, **_k) -> None:
            pass

        def __enter__(self) -> "_AlwaysFailClient":
            return self

        def __exit__(self, *_e) -> None:
            return None

        def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _DummyResponse:
            req = httpx.Request("POST", url)
            resp = httpx.Response(403, request=req)
            raise httpx.HTTPStatusError("forbidden", request=req, response=resp)

    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _AlwaysFailClient)
    assert not send_webhook_notification(
        "http://example.invalid/fail",
        {"status": "failed", "sync_id": "ctx2"},
        max_retries=0,
    )
    failed_msg = next(
        r.getMessage()
        for r in reversed(caplog.records)
        if "webhook_notify_failed" in r.getMessage()
    )
    _assert_log_contains_fields(
        failed_msg,
        (
            "log_schema_version",
            "outcome",
            "payload_type",
            "sync_id",
            "url",
            "attempt",
            "delivery_state",
            "attempt_index",
            "attempt_total",
            "retry",
            "final",
            "retry_policy",
            "retry_eligible",
            "retries_remaining",
            "http_status",
            "retry_after_seconds",
            "retry_after_source",
            "backoff_seconds",
            "retry_in_seconds",
            "retry_window_ms",
            "retry_reason",
            "error_class",
            "error_family",
            "attempt_elapsed_ms",
            "total_elapsed_ms",
        ),
    )

    # skipped path
    assert not send_webhook_notification(
        "file:///tmp/skip",
        {"status": "failed", "sync_id": "ctx3"},
    )
    skipped_msg = next(
        r.getMessage()
        for r in reversed(caplog.records)
        if "webhook_notify_skipped_invalid_url" in r.getMessage()
    )
    _assert_log_contains_fields(
        skipped_msg,
        ("log_schema_version", "payload_type", "sync_id", "skip_reason", "url"),
    )


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
    assert call["headers"]["X-TBOX-Sync-Id"] == "abc"
    ik = call["headers"]["Idempotency-Key"]
    assert len(ik) == 64
    assert all(c in "0123456789abcdef" for c in ik)
    assert call["json"]["payload_version"] == WEBHOOK_PAYLOAD_VERSION
    assert call["json"]["type"] == WEBHOOK_TYPE_TBOX_SYNC_SUMMARY
    assert "Authorization" not in call["headers"]


def test_send_webhook_notification_with_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_webhook_notification(
        "http://example.invalid/webhook",
        {"status": "failed", "sync_id": "abc"},
        bearer_token="secret-token",
    )
    assert ok
    assert _DummyClient.calls[0]["headers"]["Authorization"] == "Bearer secret-token"


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
    assert len(_DummyClient.calls[0]["headers"]["Idempotency-Key"]) == 64
    body = _DummyClient.calls[0]["json"]
    assert body["payload_version"] == WEBHOOK_PAYLOAD_VERSION
    assert body["type"] == WEBHOOK_TYPE_TBOX_RBAC_ALERT
    assert body["sync_id"] == "s1"
    assert body["status"] == "failed"
    assert body["rbac"]["reason"] == "permission_denied"
    assert body["rbac"]["rbac_alert_suppressed_in_window"] == 2
    assert "Authorization" not in _DummyClient.calls[0]["headers"]


def test_send_rbac_webhook_notification_with_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tbox_pipelines.notify.httpx.Client", _DummyClient)
    _DummyClient.calls = []

    ok = send_rbac_webhook_notification(
        "http://example.invalid/rbac-hook",
        {"sync_id": "s1", "status": "failed", "reason": "permission_denied"},
        bearer_token="rbac-secret",
    )
    assert ok
    assert _DummyClient.calls[0]["headers"]["Authorization"] == "Bearer rbac-secret"


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
