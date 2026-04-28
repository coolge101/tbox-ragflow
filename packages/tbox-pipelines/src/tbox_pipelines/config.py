from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    ragflow_base_url: str
    ragflow_api_key: str
    target_dataset_id: str
    target_dataset_name: str
    auto_create_dataset: bool
    auto_run_after_upload: bool
    http_max_retries: int
    http_retry_backoff_seconds: float
    audit_log_path: str
    rbac_audit_log_path: str
    notify_webhook_url: str
    notify_on_success: bool
    source_provider: str
    source_api_url: str
    source_api_key: str
    source_timeout_seconds: float
    actor_role: str
    rbac_policy_path: str
    rbac_policy_version: str
    rbac_policy_release_tag: str
    rbac_alert_webhook_url: str
    rbac_alert_high_risk_reasons: tuple[str, ...]
    rbac_alert_dedupe_window_seconds: int
    rbac_alert_dedupe_state_path: str


DEFAULT_CONFIG_PATH = Path("config/pipeline.sample.json")


def _to_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _to_int(value: str | int | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: str | float | int | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def _to_csv_tuple(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    return items or default


def _to_str(value: str | int | float | bool | None, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def load_config(config_path: str | None = None) -> PipelineConfig:
    env_base_url = os.getenv("RAGFLOW_BASE_URL")
    env_api_key = os.getenv("RAGFLOW_API_KEY", "")
    env_dataset_id = os.getenv("RAGFLOW_DATASET_ID", "")
    env_dataset_name = os.getenv("RAGFLOW_DATASET_NAME", "")
    env_auto_create_dataset = os.getenv("RAGFLOW_AUTO_CREATE_DATASET")
    env_auto_run = os.getenv("RAGFLOW_AUTO_RUN")
    env_http_max_retries = os.getenv("RAGFLOW_HTTP_MAX_RETRIES")
    env_http_retry_backoff = os.getenv("RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS")
    env_audit_log_path = os.getenv("RAGFLOW_AUDIT_LOG_PATH")
    env_rbac_audit_log_path = os.getenv("RAGFLOW_RBAC_AUDIT_LOG_PATH")
    env_notify_webhook_url = os.getenv("RAGFLOW_NOTIFY_WEBHOOK_URL", "")
    env_notify_on_success = os.getenv("RAGFLOW_NOTIFY_ON_SUCCESS")
    env_source_provider = os.getenv("TBOX_SOURCE_PROVIDER")
    env_source_api_url = os.getenv("TBOX_SOURCE_API_URL", "")
    env_source_api_key = os.getenv("TBOX_SOURCE_API_KEY", "")
    env_source_timeout = os.getenv("TBOX_SOURCE_TIMEOUT_SECONDS")
    env_actor_role = os.getenv("TBOX_ACTOR_ROLE")
    env_rbac_policy_path = os.getenv("TBOX_RBAC_POLICY_PATH")
    env_rbac_policy_version = os.getenv("TBOX_RBAC_POLICY_VERSION")
    env_rbac_policy_release_tag = os.getenv("TBOX_RBAC_POLICY_RELEASE_TAG")
    env_rbac_alert_webhook_url = os.getenv("TBOX_RBAC_ALERT_WEBHOOK_URL", "")
    env_rbac_alert_high_risk_reasons = os.getenv("TBOX_RBAC_ALERT_HIGH_RISK_REASONS")
    env_rbac_alert_dedupe_window = os.getenv("TBOX_RBAC_ALERT_DEDUPE_WINDOW_SECONDS")
    env_rbac_alert_dedupe_state_path = os.getenv("TBOX_RBAC_ALERT_DEDUPE_STATE_PATH")

    payload: dict[str, str | bool | int | float] = {}
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if target_path.exists():
        payload = json.loads(target_path.read_text(encoding="utf-8"))

    base_url = env_base_url or payload.get("ragflow_base_url", "http://localhost:9380")
    api_key = env_api_key or payload.get("ragflow_api_key", "")
    dataset_id = env_dataset_id or payload.get("target_dataset_id", "")
    dataset_name = env_dataset_name or payload.get("target_dataset_name", "")
    auto_create_dataset = _to_bool(
        env_auto_create_dataset,
        _to_bool(payload.get("auto_create_dataset"), True),
    )
    auto_run = _to_bool(env_auto_run, _to_bool(payload.get("auto_run_after_upload"), True))
    max_retries = _to_int(env_http_max_retries, _to_int(payload.get("http_max_retries"), 2))
    backoff = _to_float(
        env_http_retry_backoff,
        _to_float(payload.get("http_retry_backoff_seconds"), 1.0),
    )
    audit_log_path = env_audit_log_path or payload.get("audit_log_path", "logs/sync_audit.jsonl")
    rbac_audit_log_path = env_rbac_audit_log_path or payload.get(
        "rbac_audit_log_path",
        "logs/rbac_audit.jsonl",
    )
    notify_webhook_url = env_notify_webhook_url or payload.get("notify_webhook_url", "")
    notify_on_success = _to_bool(
        env_notify_on_success,
        _to_bool(payload.get("notify_on_success"), False),
    )
    source_provider = (
        str(env_source_provider or payload.get("source_provider", "stub")).strip().lower()
    )
    source_api_url = str(env_source_api_url or payload.get("source_api_url", ""))
    source_api_key = str(env_source_api_key or payload.get("source_api_key", ""))
    source_timeout_seconds = _to_float(
        env_source_timeout,
        _to_float(payload.get("source_timeout_seconds"), 15.0),
    )
    actor_role = str(env_actor_role or payload.get("actor_role", "ingest_bot")).strip().lower()
    rbac_policy_path = str(env_rbac_policy_path or payload.get("rbac_policy_path", ""))
    rbac_policy_version = str(env_rbac_policy_version or payload.get("rbac_policy_version", ""))
    rbac_policy_release_tag = str(
        env_rbac_policy_release_tag or payload.get("rbac_policy_release_tag", "")
    )
    rbac_alert_webhook_url = str(
        env_rbac_alert_webhook_url or payload.get("rbac_alert_webhook_url", "")
    )
    rbac_alert_high_risk_reasons = _to_csv_tuple(
        _to_str(env_rbac_alert_high_risk_reasons)
        or _to_str(payload.get("rbac_alert_high_risk_reasons"), "permission_denied"),
        ("permission_denied",),
    )
    rbac_alert_dedupe_window_seconds = _to_int(
        env_rbac_alert_dedupe_window,
        _to_int(payload.get("rbac_alert_dedupe_window_seconds"), 300),
    )
    rbac_alert_dedupe_state_path = _to_str(
        env_rbac_alert_dedupe_state_path
        or payload.get("rbac_alert_dedupe_state_path", "logs/rbac_alert_dedupe.json"),
    )

    return PipelineConfig(
        ragflow_base_url=str(base_url).rstrip("/"),
        ragflow_api_key=str(api_key),
        target_dataset_id=str(dataset_id),
        target_dataset_name=str(dataset_name),
        auto_create_dataset=auto_create_dataset,
        auto_run_after_upload=auto_run,
        http_max_retries=max(0, max_retries),
        http_retry_backoff_seconds=max(0.0, backoff),
        audit_log_path=str(audit_log_path),
        rbac_audit_log_path=str(rbac_audit_log_path),
        notify_webhook_url=str(notify_webhook_url),
        notify_on_success=notify_on_success,
        source_provider=source_provider,
        source_api_url=source_api_url,
        source_api_key=source_api_key,
        source_timeout_seconds=max(1.0, source_timeout_seconds),
        actor_role=actor_role or "ingest_bot",
        rbac_policy_path=rbac_policy_path,
        rbac_policy_version=rbac_policy_version,
        rbac_policy_release_tag=rbac_policy_release_tag,
        rbac_alert_webhook_url=rbac_alert_webhook_url,
        rbac_alert_high_risk_reasons=rbac_alert_high_risk_reasons,
        rbac_alert_dedupe_window_seconds=max(0, rbac_alert_dedupe_window_seconds),
        rbac_alert_dedupe_state_path=rbac_alert_dedupe_state_path,
    )
