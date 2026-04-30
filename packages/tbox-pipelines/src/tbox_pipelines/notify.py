"""Webhook HTTP notification helpers.

HTTP JSON bodies use envelope field ``payload_version`` (see ``WEBHOOK_PAYLOAD_VERSION``).
That is unrelated to ``log_version`` on ``scripts/validate_webhook_examples.sh`` stdout
lines (CI/debug; currently ``2``; see ``tests/test_validate_webhook_log_contract.py``).
See ``docs/WEBHOOK_CONTRACT.md`` Versioning.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import logging
import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

logger = logging.getLogger(__name__)

# Bump when envelope or semantics change for receivers that branch on version.
WEBHOOK_PAYLOAD_VERSION = 1
WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION = 1
WEBHOOK_RETRY_REASON_VERSION = 1

WEBHOOK_TYPE_TBOX_SYNC_SUMMARY = "tbox_sync_summary"
WEBHOOK_TYPE_TBOX_RBAC_ALERT = "tbox_rbac_alert"


def _webhook_user_agent() -> str:
    try:
        v = importlib.metadata.version("tbox-pipelines")
    except importlib.metadata.PackageNotFoundError:
        return "tbox-pipelines"
    return f"tbox-pipelines/{v}"


def _webhook_idempotency_key(payload_type: str, inner: dict[str, Any]) -> str:
    """Stable 64-char hex key for this logical POST (same across transport retries)."""
    blob = json.dumps(
        inner,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    digest = hashlib.sha256(f"{payload_type}\n{blob}".encode("utf-8")).hexdigest()
    return digest


def _webhook_post_headers(
    *,
    sync_id: str = "",
    idempotency_key: str | None = None,
    bearer_token: str | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "User-Agent": _webhook_user_agent(),
    }
    sid = str(sync_id).strip()
    if sid:
        headers["X-TBOX-Sync-Id"] = sid
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    tok = str(bearer_token or "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def _webhook_url_for_logs(url: str) -> str:
    """Strip query and fragment; mask ``user:pass@`` in ``netloc`` for log lines."""
    try:
        p = urlparse(url)
    except ValueError:
        return "<invalid_url>"
    netloc = p.netloc
    if "@" in netloc:
        hostpart = netloc.rsplit("@", 1)[1]
        netloc = f"***@{hostpart}"
    return urlunparse((p.scheme, netloc, p.path or "", "", "", ""))


def _webhook_http_url_allowed(url: str) -> bool:
    """Only allow absolute ``http``/``https`` URLs with a host (avoid ``file:`` etc.)."""
    try:
        p = urlparse(url.strip())
    except ValueError:
        return False
    if p.scheme.lower() not in ("http", "https"):
        return False
    return bool(p.netloc)


def _webhook_failure_is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (408, 429, 500, 502, 503, 504)
    return False


def _webhook_retry_reason(exc: BaseException, will_retry: bool) -> str:
    if isinstance(exc, httpx.RequestError):
        return "transport_retryable" if will_retry else "transport_non_retryable"
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if will_retry:
            return f"http_{code}"
        return f"http_non_retryable_{code}"
    return "unexpected_error"


def _webhook_retry_reason_group(exc: BaseException, will_retry: bool) -> str:
    if isinstance(exc, httpx.RequestError):
        return "transport_retryable" if will_retry else "transport_non_retryable"
    if isinstance(exc, httpx.HTTPStatusError):
        return "http_retryable" if will_retry else "http_non_retryable"
    return "unexpected"


def _webhook_failure_status_code(exc: BaseException) -> int | None:
    if isinstance(exc, httpx.HTTPStatusError):
        return int(exc.response.status_code)
    return None


def _webhook_error_class(exc: BaseException) -> str:
    return exc.__class__.__name__


def _webhook_error_family(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return "http"
    if isinstance(exc, httpx.RequestError):
        return "transport"
    return "unexpected"


@dataclass(frozen=True)
class _RetryDecision:
    will_retry: bool
    is_final: bool
    delivery_state: str
    retry_policy: str
    retry_eligible: bool
    retries_remaining: int
    retry_after_seconds: float | None
    retry_after_source: str | None
    backoff_seconds: float | None
    retry_in_seconds: float | None
    retry_window_ms: int | None


def _webhook_retry_decision(
    *,
    exc: BaseException,
    attempt: int,
    attempts: int,
    backoff: float,
) -> _RetryDecision:
    retry_eligible = _webhook_failure_is_transient(exc)
    will_retry = retry_eligible and attempt < attempts
    is_final = not will_retry
    delivery_state = "retrying" if will_retry else "failed"
    retries_remaining = max(0, attempts - attempt)

    if not will_retry:
        return _RetryDecision(
            will_retry=False,
            is_final=True,
            delivery_state="failed",
            retry_policy="none",
            retry_eligible=retry_eligible,
            retries_remaining=retries_remaining,
            retry_after_seconds=None,
            retry_after_source=None,
            backoff_seconds=None,
            retry_in_seconds=None,
            retry_window_ms=None,
        )

    backoff_seconds = backoff * attempt
    retry_after_seconds = _webhook_retry_after_seconds(exc)
    retry_after_source = "header" if retry_after_seconds is not None else None
    retry_in_seconds = backoff_seconds
    retry_policy = "backoff"
    if retry_after_seconds is not None:
        retry_in_seconds = max(retry_in_seconds, retry_after_seconds)
        if retry_in_seconds > backoff_seconds:
            retry_policy = "retry_after"
    retry_window_ms = int(retry_in_seconds * 1000) if retry_in_seconds > 0 else 0
    return _RetryDecision(
        will_retry=will_retry,
        is_final=is_final,
        delivery_state=delivery_state,
        retry_policy=retry_policy,
        retry_eligible=retry_eligible,
        retries_remaining=retries_remaining,
        retry_after_seconds=retry_after_seconds,
        retry_after_source=retry_after_source,
        backoff_seconds=backoff_seconds,
        retry_in_seconds=retry_in_seconds,
        retry_window_ms=retry_window_ms,
    )


def _webhook_retry_after_seconds(exc: BaseException) -> float | None:
    """Best-effort parse ``Retry-After`` seconds or HTTP-date from failures."""
    if not isinstance(exc, httpx.HTTPStatusError):
        return None
    raw = exc.response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        pass
    else:
        if seconds > 0:
            return seconds
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    delta = when.timestamp() - time.time()
    if delta <= 0:
        return None
    return delta


def _post_webhook_json(
    webhook_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    *,
    timeout_seconds: float,
    max_retries: int,
    retry_backoff_seconds: float,
) -> bool:
    attempts = max(1, max(0, max_retries) + 1)
    backoff = max(0.0, retry_backoff_seconds)
    log_url = _webhook_url_for_logs(webhook_url)
    payload_type = str(payload.get("type", "") or "unknown")
    sync_id = str(payload.get("sync_id", "") or "")
    started_at = time.monotonic()
    for attempt in range(1, attempts + 1):
        attempt_started_at = time.monotonic()
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(webhook_url, headers=headers, json=payload)
                response.raise_for_status()
            attempt_elapsed_ms = int((time.monotonic() - attempt_started_at) * 1000)
            total_elapsed_ms = int((time.monotonic() - started_at) * 1000)
            logger.debug(
                "webhook_notify_ok log_schema_version=%s outcome=%s payload_type=%s sync_id=%s "
                "url=%s http_status=%s "
                "delivery_state=%s attempt=%s/%s attempt_index=%s attempt_total=%s "
                "attempt_elapsed_ms=%s total_elapsed_ms=%s",
                WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION,
                "success",
                payload_type,
                sync_id,
                log_url,
                response.status_code,
                "delivered",
                attempt,
                attempts,
                attempt,
                attempts,
                attempt_elapsed_ms,
                total_elapsed_ms,
            )
            return True
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            attempt_elapsed_ms = int((time.monotonic() - attempt_started_at) * 1000)
            total_elapsed_ms = int((time.monotonic() - started_at) * 1000)
            decision = _webhook_retry_decision(
                exc=exc,
                attempt=attempt,
                attempts=attempts,
                backoff=backoff,
            )
            retry_reason = _webhook_retry_reason(exc, decision.will_retry)
            retry_reason_group = _webhook_retry_reason_group(exc, decision.will_retry)
            error_class = _webhook_error_class(exc)
            error_family = _webhook_error_family(exc)
            http_status = _webhook_failure_status_code(exc)
            logger.warning(
                "webhook_notify_failed log_schema_version=%s outcome=%s payload_type=%s sync_id=%s "
                "url=%s attempt=%s/%s "
                "delivery_state=%s attempt_index=%s attempt_total=%s retry=%s final=%s "
                "retry_policy=%s "
                "retry_eligible=%s retries_remaining=%s http_status=%s "
                "retry_after_seconds=%s retry_after_source=%s backoff_seconds=%s "
                "retry_in_seconds=%s retry_window_ms=%s "
                "retry_reason=%s retry_reason_group=%s retry_reason_version=%s "
                "error_class=%s error_family=%s "
                "attempt_elapsed_ms=%s total_elapsed_ms=%s error=%s",
                WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION,
                "failure",
                payload_type,
                sync_id,
                log_url,
                attempt,
                attempts,
                decision.delivery_state,
                attempt,
                attempts,
                decision.will_retry,
                decision.is_final,
                decision.retry_policy,
                decision.retry_eligible,
                decision.retries_remaining,
                http_status,
                decision.retry_after_seconds,
                decision.retry_after_source,
                decision.backoff_seconds,
                decision.retry_in_seconds,
                decision.retry_window_ms,
                retry_reason,
                retry_reason_group,
                WEBHOOK_RETRY_REASON_VERSION,
                error_class,
                error_family,
                attempt_elapsed_ms,
                total_elapsed_ms,
                exc,
            )
            if not decision.will_retry:
                return False
            if decision.retry_in_seconds and decision.retry_in_seconds > 0:
                time.sleep(decision.retry_in_seconds)
        except Exception as exc:  # noqa: BLE001
            attempt_elapsed_ms = int((time.monotonic() - attempt_started_at) * 1000)
            total_elapsed_ms = int((time.monotonic() - started_at) * 1000)
            logger.warning(
                "webhook_notify_failed log_schema_version=%s outcome=%s payload_type=%s sync_id=%s "
                "url=%s attempt=%s/%s "
                "delivery_state=%s attempt_index=%s attempt_total=%s retry=%s final=%s "
                "retry_policy=%s "
                "retry_eligible=%s retries_remaining=%s http_status=%s "
                "retry_after_seconds=%s retry_after_source=%s backoff_seconds=%s "
                "retry_in_seconds=%s retry_window_ms=%s "
                "retry_reason=%s retry_reason_group=%s retry_reason_version=%s "
                "error_class=%s error_family=%s "
                "attempt_elapsed_ms=%s total_elapsed_ms=%s error=%s",
                WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION,
                "failure",
                payload_type,
                sync_id,
                log_url,
                attempt,
                attempts,
                "failed",
                attempt,
                attempts,
                False,
                True,
                "none",
                False,
                0,
                None,
                None,
                None,
                None,
                None,
                "unexpected_error",
                "unexpected",
                WEBHOOK_RETRY_REASON_VERSION,
                _webhook_error_class(exc),
                _webhook_error_family(exc),
                attempt_elapsed_ms,
                total_elapsed_ms,
                exc,
            )
            return False
    return False


def build_tbox_sync_summary_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Assemble POST JSON for ``tbox_sync_summary`` (must match ``webhook_payload.schema.json``)."""
    return {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
        "status": summary.get("status", "unknown"),
        "sync_id": summary.get("sync_id", ""),
        "summary": summary,
    }


def build_tbox_rbac_alert_payload(rbac_event: dict[str, Any]) -> dict[str, Any]:
    """Assemble POST JSON for ``tbox_rbac_alert`` (must match ``webhook_payload.schema.json``)."""
    return {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": WEBHOOK_TYPE_TBOX_RBAC_ALERT,
        "status": rbac_event.get("status", "unknown"),
        "sync_id": rbac_event.get("sync_id", ""),
        "rbac": rbac_event,
    }


def send_webhook_notification(
    webhook_url: str,
    summary: dict[str, Any],
    timeout_seconds: float = 10.0,
    *,
    bearer_token: str | None = None,
    max_retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> bool:
    if not webhook_url:
        return False
    sync_id = str(summary.get("sync_id", "") or "")
    if not _webhook_http_url_allowed(webhook_url):
        logger.warning(
            "webhook_notify_skipped_invalid_url log_schema_version=%s payload_type=%s "
            "sync_id=%s skip_reason=%s url=%s",
            WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION,
            WEBHOOK_TYPE_TBOX_SYNC_SUMMARY,
            sync_id,
            "invalid_url",
            _webhook_url_for_logs(webhook_url),
        )
        return False

    payload = build_tbox_sync_summary_payload(summary)
    idem = _webhook_idempotency_key(WEBHOOK_TYPE_TBOX_SYNC_SUMMARY, summary)
    headers = _webhook_post_headers(
        sync_id=sync_id,
        idempotency_key=idem,
        bearer_token=bearer_token,
    )

    return _post_webhook_json(
        webhook_url,
        headers,
        payload,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def send_rbac_webhook_notification(
    webhook_url: str,
    rbac_event: dict[str, Any],
    timeout_seconds: float = 10.0,
    *,
    bearer_token: str | None = None,
    max_retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> bool:
    if not webhook_url:
        return False
    sync_id = str(rbac_event.get("sync_id", "") or "")
    if not _webhook_http_url_allowed(webhook_url):
        logger.warning(
            "webhook_notify_skipped_invalid_url log_schema_version=%s payload_type=%s "
            "sync_id=%s skip_reason=%s url=%s",
            WEBHOOK_NOTIFY_LOG_SCHEMA_VERSION,
            WEBHOOK_TYPE_TBOX_RBAC_ALERT,
            sync_id,
            "invalid_url",
            _webhook_url_for_logs(webhook_url),
        )
        return False

    payload = build_tbox_rbac_alert_payload(rbac_event)
    idem = _webhook_idempotency_key(WEBHOOK_TYPE_TBOX_RBAC_ALERT, rbac_event)
    headers = _webhook_post_headers(
        sync_id=sync_id,
        idempotency_key=idem,
        bearer_token=bearer_token,
    )

    return _post_webhook_json(
        webhook_url,
        headers,
        payload,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def should_notify(summary: dict[str, Any], notify_on_success: bool) -> bool:
    status = summary.get("status")
    if status == "ok":
        return notify_on_success
    return True


def should_notify_rbac_event(event: dict[str, Any], high_risk_reasons: tuple[str, ...]) -> bool:
    status = str(event.get("status", ""))
    reason = str(event.get("reason", ""))
    return status == "failed" and reason in set(high_risk_reasons)
