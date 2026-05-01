from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

_GOOD_METRICS = {
    "event": "alert_docs_gate_ok",
    "summary_version": 1,
    "metrics_emit_version": 1,
    "required_example_files": 0,
    "required_stage_rules": 0,
    "examples_readme_required_tokens": 0,
}


def _pkg_env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(_ROOT / "src")}


def test_alert_docs_gate_ci_succeeds(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "tbox_pipelines.alert_docs_gate_cli",
            "ci",
            "--verbose",
            "--log-path",
            str(log_path),
            "--emit-json",
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert res.returncode == 0, res.stderr
    assert "alert_docs_gate_metrics event=" in res.stdout
    assert "alert_docs_gate_metrics_json " in res.stdout
    text = log_path.read_text(encoding="utf-8")
    assert "validate_alert_docs_links.py: ok" in text
    assert "validate_alert_docs_links.py: summary " in text


def test_alert_docs_gate_metrics_validate_matches_standalone_module() -> None:
    payload = json.dumps(_GOOD_METRICS, ensure_ascii=True)
    gate = subprocess.run(
        [
            sys.executable,
            "-m",
            "tbox_pipelines.alert_docs_gate_cli",
            "metrics-validate",
        ],
        cwd=_ROOT,
        input=payload,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    direct = subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.metrics_payload_validate_cli"],
        cwd=_ROOT,
        input=payload,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert gate.returncode == 0
    assert direct.returncode == 0
    assert gate.stdout == direct.stdout


def test_alert_docs_gate_emit_forwards_to_metrics_emit_cli(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    validate = subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.alert_docs_links_validate_cli", "--verbose"],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert validate.returncode == 0, validate.stderr
    log_path.write_text(validate.stdout, encoding="utf-8")

    gate = subprocess.run(
        [
            sys.executable,
            "-m",
            "tbox_pipelines.alert_docs_gate_cli",
            "emit",
            "--log-path",
            str(log_path),
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    direct = subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.metrics_emit_cli", "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert gate.returncode == 0, gate.stderr
    assert direct.returncode == 0, direct.stderr
    assert gate.stdout == direct.stdout


def test_alert_docs_gate_validate_matches_standalone_verbose() -> None:
    gate = subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.alert_docs_gate_cli", "validate", "--verbose"],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    direct = subprocess.run(
        [sys.executable, "-m", "tbox_pipelines.alert_docs_links_validate_cli", "--verbose"],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_pkg_env(),
    )
    assert gate.returncode == 0
    assert direct.returncode == 0
    assert gate.stdout == direct.stdout
