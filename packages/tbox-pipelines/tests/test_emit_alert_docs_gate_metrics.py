from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VALIDATE_SCRIPT = _ROOT / "scripts" / "validate_alert_docs_links.py"
_EMIT_SCRIPT = _ROOT / "scripts" / "emit_alert_docs_gate_metrics.py"
_RULES = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.json"


def test_emit_alert_docs_gate_metrics_from_validator_output(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    validate_res = subprocess.run(
        [sys.executable, str(_VALIDATE_SCRIPT), "--verbose"],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert validate_res.returncode == 0, validate_res.stderr
    log_path.write_text(validate_res.stdout, encoding="utf-8")

    emit_res = subprocess.run(
        [sys.executable, str(_EMIT_SCRIPT), "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert emit_res.returncode == 0, emit_res.stderr
    assert emit_res.stdout.startswith(
        "alert_docs_gate_metrics event=alert_docs_gate_ok summary_version=1 "
    )
    assert "required_example_files=" in emit_res.stdout
    assert "required_stage_rules=" in emit_res.stdout
    assert "examples_readme_required_tokens=" in emit_res.stdout


def test_emit_alert_docs_gate_metrics_enforces_contract_keys(tmp_path: Path) -> None:
    rules = json.loads(_RULES.read_text(encoding="utf-8"))
    summary_contract = rules["summary_contract"]
    payload = {
        "event": summary_contract["event"],
        "summary_version": summary_contract["summary_version"],
        summary_contract["metric_keys"][0]: 1,
        summary_contract["metric_keys"][1]: 2,
        summary_contract["metric_keys"][2]: 3,
        "unknown_metric": 99,
    }
    log_path = tmp_path / "alert_docs_gate.log"
    log_path.write_text(
        "validate_alert_docs_links.py: summary "
        + json.dumps(payload, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )

    emit_res = subprocess.run(
        [sys.executable, str(_EMIT_SCRIPT), "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert emit_res.returncode != 0
    assert "summary payload has unexpected key(s): unknown_metric" in emit_res.stderr


def test_emit_alert_docs_gate_metrics_missing_summary_line_fails(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    log_path.write_text("validate_alert_docs_links.py: verbose noop\n", encoding="utf-8")

    emit_res = subprocess.run(
        [sys.executable, str(_EMIT_SCRIPT), "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert emit_res.returncode != 0
    assert "missing alert docs gate summary line" in emit_res.stderr
