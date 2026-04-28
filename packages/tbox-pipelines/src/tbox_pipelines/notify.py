from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def send_webhook_notification(
    webhook_url: str,
    summary: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> bool:
    if not webhook_url:
        return False

    payload = {
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


def should_notify(summary: dict[str, Any], notify_on_success: bool) -> bool:
    status = summary.get("status")
    if status == "ok":
        return notify_on_success
    return True
