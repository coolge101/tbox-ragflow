from __future__ import annotations

import json
from pathlib import Path

import pytest

from tbox_pipelines.config import load_config

_SAMPLE = Path(__file__).resolve().parent.parent / "config" / "pipeline.sample.json"


def _base_payload() -> dict:
    return json.loads(_SAMPLE.read_text(encoding="utf-8"))


def test_notify_webhook_timeouts_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    data = _base_payload()
    data.pop("notify_webhook_timeout_seconds", None)
    data.pop("rbac_alert_webhook_timeout_seconds", None)
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.notify_webhook_timeout_seconds == 10.0
    assert cfg.rbac_alert_webhook_timeout_seconds == 10.0


def test_notify_webhook_timeouts_from_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    data = _base_payload()
    data["notify_webhook_timeout_seconds"] = 25.5
    data["rbac_alert_webhook_timeout_seconds"] = 7
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.notify_webhook_timeout_seconds == 25.5
    assert cfg.rbac_alert_webhook_timeout_seconds == 7.0


def test_notify_webhook_timeouts_env_overrides_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _base_payload()
    data["notify_webhook_timeout_seconds"] = 99.0
    data["rbac_alert_webhook_timeout_seconds"] = 99.0
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS", "4.5")
    cfg = load_config(str(p))
    assert cfg.notify_webhook_timeout_seconds == 3.0
    assert cfg.rbac_alert_webhook_timeout_seconds == 4.5


def test_webhook_retries_inherit_http_when_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("RAGFLOW_HTTP_MAX_RETRIES", raising=False)
    monkeypatch.delenv("RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS", raising=False)
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_RETRY_BACKOFF_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_RETRY_BACKOFF_SECONDS", raising=False)
    data = _base_payload()
    for k in (
        "notify_webhook_max_retries",
        "notify_webhook_retry_backoff_seconds",
        "rbac_alert_webhook_max_retries",
        "rbac_alert_webhook_retry_backoff_seconds",
    ):
        data.pop(k, None)
    data["http_max_retries"] = 5
    data["http_retry_backoff_seconds"] = 2.5
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.http_max_retries == 5
    assert cfg.notify_webhook_max_retries == 5
    assert cfg.notify_webhook_retry_backoff_seconds == 2.5
    assert cfg.rbac_alert_webhook_max_retries == 5
    assert cfg.rbac_alert_webhook_retry_backoff_seconds == 2.5


def test_webhook_retries_env_override_independent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("RAGFLOW_HTTP_MAX_RETRIES", raising=False)
    monkeypatch.delenv("RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS", raising=False)
    data = _base_payload()
    data["http_max_retries"] = 1
    data["http_retry_backoff_seconds"] = 1.0
    data["notify_webhook_max_retries"] = 9
    data["rbac_alert_webhook_max_retries"] = 9
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES", "0")
    monkeypatch.setenv("RAGFLOW_NOTIFY_WEBHOOK_RETRY_BACKOFF_SECONDS", "0.25")
    monkeypatch.setenv("TBOX_RBAC_ALERT_WEBHOOK_MAX_RETRIES", "7")
    monkeypatch.setenv("TBOX_RBAC_ALERT_WEBHOOK_RETRY_BACKOFF_SECONDS", "3")
    cfg = load_config(str(p))
    assert cfg.http_max_retries == 1
    assert cfg.notify_webhook_max_retries == 0
    assert cfg.notify_webhook_retry_backoff_seconds == 0.25
    assert cfg.rbac_alert_webhook_max_retries == 7
    assert cfg.rbac_alert_webhook_retry_backoff_seconds == 3.0


def test_notify_webhook_timeouts_clamped_minimum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _base_payload()
    data["notify_webhook_timeout_seconds"] = 0.01
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_RETRY_BACKOFF_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_RETRY_BACKOFF_SECONDS", raising=False)
    cfg = load_config(str(p))
    assert cfg.notify_webhook_timeout_seconds == 1.0
