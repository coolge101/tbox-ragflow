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
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Bump when envelope or semantics change for receivers that branch on version.
WEBHOOK_PAYLOAD_VERSION = 1

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
    blob = json.dumps(inner, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(f"{payload_type}\n{blob}".encode("utf-8")).hexdigest()
    return digest


def _webhook_post_headers(
    *,
    sync_id: str = "",
    idempotency_key: str | None = None,
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
    return headers


def _webhook_failure_is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (408, 429, 500, 502, 503, 504)
    return False


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
    for attempt in range(1, attempts + 1):
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(webhook_url, headers=headers, json=payload)
                response.raise_for_status()
            return True
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            will_retry = _webhook_failure_is_transient(exc) and attempt < attempts
            logger.warning(
                "webhook_notify_failed url=%s attempt=%s/%s retry=%s error=%s",
                webhook_url,
                attempt,
                attempts,
                will_retry,
                exc,
            )
            if not will_retry:
                return False
            if backoff > 0:
                time.sleep(backoff * attempt)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "webhook_notify_failed url=%s attempt=%s/%s retry=%s error=%s",
                webhook_url,
                attempt,
                attempts,
                False,
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
    max_retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> bool:
    if not webhook_url:
        return False

    payload = build_tbox_sync_summary_payload(summary)
    sync_id = str(summary.get("sync_id", "") or "")
    idem = _webhook_idempotency_key(WEBHOOK_TYPE_TBOX_SYNC_SUMMARY, summary)
    headers = _webhook_post_headers(sync_id=sync_id, idempotency_key=idem)

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
    max_retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> bool:
    if not webhook_url:
        return False

    payload = build_tbox_rbac_alert_payload(rbac_event)
    sync_id = str(rbac_event.get("sync_id", "") or "")
    idem = _webhook_idempotency_key(WEBHOOK_TYPE_TBOX_RBAC_ALERT, rbac_event)
    headers = _webhook_post_headers(sync_id=sync_id, idempotency_key=idem)

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
