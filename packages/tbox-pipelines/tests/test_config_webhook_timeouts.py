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


def test_notify_webhook_timeouts_clamped_minimum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _base_payload()
    data["notify_webhook_timeout_seconds"] = 0.01
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.delenv("RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS", raising=False)
    cfg = load_config(str(p))
    assert cfg.notify_webhook_timeout_seconds == 1.0
