from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Bump when envelope or semantics change for receivers that branch on version.
WEBHOOK_PAYLOAD_VERSION = 1


def send_webhook_notification(
    webhook_url: str,
    summary: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> bool:
    if not webhook_url:
        return False

    payload = {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": "tbox_sync_summary",
        "status": summary.get("status", "unknown"),
        "sync_id": summary.get("sync_id", ""),
        "summary": summary,
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
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

    payload = {
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "type": "tbox_rbac_alert",
        "status": rbac_event.get("status", "unknown"),
        "sync_id": rbac_event.get("sync_id", ""),
        "rbac": rbac_event,
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
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
