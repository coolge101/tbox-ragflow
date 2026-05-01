from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VALIDATE = _ROOT / "scripts" / "validate_alert_docs_metrics_payload.py"


def _pkg_env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(_ROOT / "src")}


_GOOD = {
    "event": "alert_docs_gate_ok",
    "summary_version": 1,
    "metrics_emit_version": 1,
    "required_example_files": 0,
    "required_stage_rules": 0,
    "examples_readme_required_tokens": 0,
}


def _run_payload(data: object) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(_VALIDATE)]
    return subprocess.run(
        cmd,
        cwd=_ROOT,
        input=json.dumps(data, ensure_ascii=True),
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )


def _run_payload_module(data: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.metrics_payload_validate_cli"],
        cwd=_ROOT,
        input=json.dumps(data, ensure_ascii=True),
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )


def test_validate_alert_docs_metrics_payload_ok_stdin() -> None:
    res = _run_payload(_GOOD)
    assert res.returncode == 0, res.stderr
    assert "validate_alert_docs_metrics_payload.py: ok" in res.stdout


def test_validate_alert_docs_metrics_payload_ok_stdin_via_module() -> None:
    res = _run_payload_module(_GOOD)
    assert res.returncode == 0, res.stderr
    assert "validate_alert_docs_metrics_payload.py: ok" in res.stdout


def test_validate_alert_docs_metrics_payload_rejects_extra_key() -> None:
    bad = {**_GOOD, "extra": 1}
    res = _run_payload(bad)
    assert res.returncode == 1
    assert "unexpected key" in res.stderr


def test_validate_alert_docs_metrics_payload_rejects_wrong_event() -> None:
    bad = {**_GOOD, "event": "other"}
    res = _run_payload(bad)
    assert res.returncode == 1
    assert "must equal" in res.stderr


def test_validate_alert_docs_metrics_payload_empty_stdin_fails() -> None:
    res = subprocess.run(
        [sys.executable, str(_VALIDATE)],
        cwd=_ROOT,
        input="",
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert res.returncode == 1
    assert "empty payload" in res.stderr
