from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from tbox_pipelines.audit import append_audit_record, append_rbac_audit_record
from tbox_pipelines.config import load_config
from tbox_pipelines.ingest.sources import fetch_documents
from tbox_pipelines.notify import (
    send_rbac_webhook_notification,
    send_webhook_notification,
    should_notify,
    should_notify_rbac_event,
)
from tbox_pipelines.ragflow.client import RagflowClient
from tbox_pipelines.rbac import (
    configure_policy_from_file,
    get_policy_meta,
    require_permission,
    set_policy_labels,
)

logger = logging.getLogger(__name__)


class SyncConfigError(ValueError):
    """Raised when required sync configuration is missing or invalid."""


def _emit_sync_summary(summary: dict[str, Any], config) -> None:
    logger.info("sync_summary %s", json.dumps(summary, ensure_ascii=False))
    append_audit_record(config.audit_log_path, summary)
    if should_notify(summary, notify_on_success=config.notify_on_success):
        notified = send_webhook_notification(config.notify_webhook_url, summary)
        logger.info(
            "sync_notify status=%s sync_id=%s notified=%s",
            summary.get("status"),
            summary.get("sync_id"),
            notified,
        )


def _emit_rbac_event(
    *,
    sync_id: str,
    status: str,
    reason: str,
    actor_role: str,
    policy_meta: dict[str, Any],
    config,
    error: str = "",
) -> None:
    event = {
        "sync_id": sync_id,
        "status": status,
        "reason": reason,
        "actor_role": actor_role,
        **policy_meta,
    }
    if error:
        event["error"] = error
    append_rbac_audit_record(config.rbac_audit_log_path, event)
    should_alert = should_notify_rbac_event(event, config.rbac_alert_high_risk_reasons)
    if not should_alert:
        return
    emit, suppressed_in_window = _apply_rbac_alert_dedupe(event, config)
    if not emit:
        return
    webhook_payload = {**event, "rbac_alert_suppressed_in_window": suppressed_in_window}
    notified = send_rbac_webhook_notification(config.rbac_alert_webhook_url, webhook_payload)
    if suppressed_in_window > 0:
        logger.info(
            "rbac_notify_aggregate suppressed_in_window=%s reason=%s sync_id=%s",
            suppressed_in_window,
            event.get("reason"),
            event.get("sync_id"),
        )
    logger.info(
        "rbac_notify reason=%s sync_id=%s notified=%s",
        event.get("reason"),
        event.get("sync_id"),
        notified,
    )


def _rbac_dedupe_key(event: dict[str, Any]) -> str:
    return "|".join(
        [
            str(event.get("reason", "")),
            str(event.get("rbac_policy_fingerprint", "")),
            str(event.get("actor_role", "")),
        ]
    )


def _load_rbac_dedupe_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _normalize_dedupe_entry(raw: Any) -> dict[str, int]:
    if isinstance(raw, dict):
        return {
            "last_sent_ts": int(raw.get("last_sent_ts", 0)),
            "suppressed_count": int(raw.get("suppressed_count", 0)),
        }
    if isinstance(raw, int):
        return {"last_sent_ts": raw, "suppressed_count": 0}
    return {"last_sent_ts": 0, "suppressed_count": 0}


def _apply_rbac_alert_dedupe(event: dict[str, Any], config) -> tuple[bool, int]:
    """Return (emit_webhook, suppressed_count_since_last_emit)."""
    dedupe_window = int(config.rbac_alert_dedupe_window_seconds)
    if dedupe_window <= 0:
        return True, 0
    key = _rbac_dedupe_key(event)
    now = int(time.time())
    state_path = Path(config.rbac_alert_dedupe_state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = _load_rbac_dedupe_state(state_path)

    entry = _normalize_dedupe_entry(state.get(key))
    last_ts = entry["last_sent_ts"]
    suppressed = entry["suppressed_count"]

    if last_ts > 0 and now - last_ts < dedupe_window:
        entry["suppressed_count"] = suppressed + 1
        state[key] = entry
        state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        logger.info(
            "rbac_notify_suppressed key=%s dedupe_window=%s suppressed_count=%s",
            key,
            dedupe_window,
            entry["suppressed_count"],
        )
        return False, 0

    suppressed_for_payload = suppressed
    state[key] = {"last_sent_ts": now, "suppressed_count": 0}
    state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    return True, suppressed_for_payload


def run_sync(config_path: str | None = None) -> int:
    sync_id = uuid.uuid4().hex
    config = load_config(config_path)
    role = config.actor_role
    policy_meta = get_policy_meta()
    try:
        configure_policy_from_file(config.rbac_policy_path)
        set_policy_labels(
            version=config.rbac_policy_version,
            release_tag=config.rbac_policy_release_tag,
        )
        policy_meta = get_policy_meta()
        _emit_rbac_event(
            sync_id=sync_id,
            status="ok",
            reason="policy_loaded",
            actor_role=role,
            policy_meta=policy_meta,
            config=config,
        )
        require_permission(role, "sync:run")
        if config.source_provider == "http_json":
            require_permission(role, "source:http_json")
        if config.auto_create_dataset:
            require_permission(role, "dataset:auto_create")
        if config.auto_run_after_upload:
            require_permission(role, "ragflow:run_documents")
    except ValueError as exc:
        _emit_rbac_event(
            sync_id=sync_id,
            status="failed",
            reason="rbac_policy_invalid",
            actor_role=role,
            policy_meta=policy_meta,
            config=config,
            error=str(exc),
        )
        summary = {
            "sync_id": sync_id,
            "documents_fetched": 0,
            "resolved_dataset_id": "",
            "uploaded_doc_ids": [],
            "run_triggered": False,
            "auto_run_after_upload": config.auto_run_after_upload,
            "status": "failed",
            "reason": "rbac_policy_invalid",
            "actor_role": role,
            "error": str(exc),
            **policy_meta,
        }
        _emit_sync_summary(summary, config)
        raise SyncConfigError(str(exc)) from exc
    except PermissionError as exc:
        _emit_rbac_event(
            sync_id=sync_id,
            status="failed",
            reason="permission_denied",
            actor_role=role,
            policy_meta=policy_meta,
            config=config,
            error=str(exc),
        )
        summary = {
            "sync_id": sync_id,
            "documents_fetched": 0,
            "resolved_dataset_id": "",
            "uploaded_doc_ids": [],
            "run_triggered": False,
            "auto_run_after_upload": config.auto_run_after_upload,
            "status": "failed",
            "reason": "permission_denied",
            "actor_role": role,
            "error": str(exc),
            **policy_meta,
        }
        _emit_sync_summary(summary, config)
        raise SyncConfigError(str(exc)) from exc

    docs = fetch_documents(
        provider=config.source_provider,
        source_api_url=config.source_api_url,
        source_api_key=config.source_api_key,
        timeout_seconds=config.source_timeout_seconds,
    )
    client = RagflowClient(
        base_url=config.ragflow_base_url,
        api_key=config.ragflow_api_key,
        max_retries=config.http_max_retries,
        retry_backoff_seconds=config.http_retry_backoff_seconds,
    )

    resolved_dataset_id = client.resolve_dataset_id(
        dataset_id=config.target_dataset_id,
        dataset_name=config.target_dataset_name,
        auto_create=config.auto_create_dataset,
    )
    if not resolved_dataset_id:
        summary = {
            "sync_id": sync_id,
            "documents_fetched": len(docs),
            "resolved_dataset_id": "",
            "uploaded_doc_ids": [],
            "run_triggered": False,
            "auto_run_after_upload": config.auto_run_after_upload,
            "status": "failed",
            "reason": "dataset_not_resolved",
            **policy_meta,
        }
        _emit_sync_summary(summary, config)
        raise SyncConfigError(
            "Unable to resolve target dataset id. Set RAGFLOW_DATASET_ID or RAGFLOW_DATASET_NAME."
        )

    doc_ids = client.upload_documents(
        dataset_id=resolved_dataset_id,
        documents=docs,
        sync_id=sync_id,
    )

    run_triggered = False
    if config.auto_run_after_upload:
        client.run_documents(doc_ids, sync_id=sync_id)
        run_triggered = bool(doc_ids)

    summary = {
        "sync_id": sync_id,
        "actor_role": role,
        "documents_fetched": len(docs),
        "resolved_dataset_id": resolved_dataset_id,
        "uploaded_doc_ids": doc_ids,
        "run_triggered": run_triggered,
        "auto_run_after_upload": config.auto_run_after_upload,
        "status": "ok",
        **policy_meta,
    }
    _emit_sync_summary(summary, config)
    return len(docs)
