"""Webhook HTTP notification helpers.

HTTP JSON bodies use envelope field ``payload_version`` (see ``WEBHOOK_PAYLOAD_VERSION``).
That is unrelated to ``log_version`` on ``scripts/validate_webhook_examples.sh`` stdout
lines (CI/debug; currently ``2``; see ``tests/test_validate_webhook_log_contract.py``).
See ``docs/WEBHOOK_CONTRACT.md`` Versioning.
"""

from __future__ import annotations

import importlib.metadata
import logging
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


def _webhook_post_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "User-Agent": _webhook_user_agent(),
    }


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
) -> bool:
    if not webhook_url:
        return False

    payload = build_tbox_sync_summary_payload(summary)

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                webhook_url,
                headers=_webhook_post_headers(),
                json=payload,
            )
            response.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("webhook_notify_failed url=%s error=%s", webhook_url, exc)
        return False


def send_rbac_webhook_notification(
    webhook_url: str,
    rbac_event: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> bool:
    if not webhook_url:
        return False

    payload = build_tbox_rbac_alert_payload(rbac_event)

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                webhook_url,
                headers=_webhook_post_headers(),
                json=payload,
            )
            response.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("webhook_notify_failed url=%s error=%s", webhook_url, exc)
        return False


def should_notify(summary: dict[str, Any], notify_on_success: bool) -> bool:
    status = summary.get("status")
    if status == "ok":
        return notify_on_success
    return True


def should_notify_rbac_event(event: dict[str, Any], high_risk_reasons: tuple[str, ...]) -> bool:
    status = str(event.get("status", ""))
    reason = str(event.get("reason", ""))
    return status == "failed" and reason in set(high_risk_reasons)
