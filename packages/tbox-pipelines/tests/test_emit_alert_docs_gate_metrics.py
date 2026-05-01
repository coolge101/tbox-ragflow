from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VALIDATE_SCRIPT = _ROOT / "scripts" / "validate_alert_docs_links.py"
_EMIT_SCRIPT = _ROOT / "scripts" / "emit_alert_docs_gate_metrics.py"
_RULES = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.json"


def _emit_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = {**os.environ, "PYTHONPATH": str(_ROOT / "src")}
    if overrides:
        env.update(overrides)
    return env


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
        env=_emit_env(),
    )
    assert emit_res.returncode == 0, emit_res.stderr
    assert emit_res.stdout.startswith(
        "alert_docs_gate_metrics event=alert_docs_gate_ok summary_version=1 metrics_emit_version=1 "
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
        "validate_alert_docs_links.py: summary " + json.dumps(payload, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    emit_res = subprocess.run(
        [sys.executable, str(_EMIT_SCRIPT), "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env(),
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
        env=_emit_env(),
    )
    assert emit_res.returncode != 0
    assert "missing alert docs gate summary line" in emit_res.stderr


def test_emit_alert_docs_gate_metrics_json_mirror_output(tmp_path: Path) -> None:
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
        [
            sys.executable,
            str(_EMIT_SCRIPT),
            "--log-path",
            str(log_path),
            "--emit-json",
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env(),
    )
    assert emit_res.returncode == 0, emit_res.stderr
    lines = [line for line in emit_res.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0].startswith("alert_docs_gate_metrics ")
    assert lines[1].startswith("alert_docs_gate_metrics_json ")

    json_payload = json.loads(lines[1][len("alert_docs_gate_metrics_json ") :])
    rules = json.loads(_RULES.read_text(encoding="utf-8"))
    summary_contract = rules["summary_contract"]
    assert json_payload["event"] == summary_contract["event"]
    assert json_payload["summary_version"] == summary_contract["summary_version"]
    assert json_payload.get("metrics_emit_version") == 1
    for key in summary_contract["metric_keys"]:
        assert isinstance(json_payload[key], int)


def test_emit_alert_docs_gate_metrics_enforces_metric_value_type(tmp_path: Path) -> None:
    rules = json.loads(_RULES.read_text(encoding="utf-8"))
    summary_contract = rules["summary_contract"]
    metric_keys = summary_contract["metric_keys"]
    payload = {
        "event": summary_contract["event"],
        "summary_version": summary_contract["summary_version"],
        metric_keys[0]: 1,
        metric_keys[1]: -1,
        metric_keys[2]: "3",
    }
    log_path = tmp_path / "alert_docs_gate.log"
    log_path.write_text(
        "validate_alert_docs_links.py: summary " + json.dumps(payload, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    emit_res = subprocess.run(
        [sys.executable, str(_EMIT_SCRIPT), "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env(),
    )
    assert emit_res.returncode != 0
    assert (
        "summary payload metric value must be a non-negative integer for key(s): "
        f"{metric_keys[1]},{metric_keys[2]}"
    ) in emit_res.stderr


def test_emit_alert_docs_gate_metrics_writes_github_output(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    gh_out = tmp_path / "github_output.txt"
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
        [
            sys.executable,
            str(_EMIT_SCRIPT),
            "--log-path",
            str(log_path),
            "--emit-json",
            "--write-github-output",
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env({"GITHUB_OUTPUT": str(gh_out)}),
    )
    assert emit_res.returncode == 0, emit_res.stderr
    text = gh_out.read_text(encoding="utf-8")
    assert "alert_docs_gate_metrics_kv<<" in text
    assert "alert_docs_gate_metrics_json_line<<" in text
    assert "alert_docs_gate_metrics_json<<" in text


def test_emit_alert_docs_gate_metrics_fails_on_schema_mismatch(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    bad_schema = tmp_path / "bad_metrics.schema.json"
    bad_schema.write_text(
        json.dumps(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["event", "summary_version", "metrics_emit_version", "bogus"],
                "properties": {
                    "event": {"type": "string", "minLength": 1},
                    "summary_version": {"type": "integer", "minimum": 1},
                    "metrics_emit_version": {"type": "integer", "minimum": 1},
                    "required_example_files": {"type": "integer", "minimum": 0},
                    "required_stage_rules": {"type": "integer", "minimum": 0},
                    "examples_readme_required_tokens": {"type": "integer", "minimum": 0},
                    "bogus": {"type": "integer", "minimum": 0},
                },
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
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
        env=_emit_env({"ALERT_DOCS_GATE_METRICS_SCHEMA_PATH": str(bad_schema)}),
    )
    assert emit_res.returncode != 0
    assert "metrics payload missing required key: bogus" in emit_res.stderr


def test_emit_alert_docs_gate_metrics_writes_step_summary(tmp_path: Path) -> None:
    log_path = tmp_path / "alert_docs_gate.log"
    step_summary = tmp_path / "step_summary.md"
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
        [
            sys.executable,
            str(_EMIT_SCRIPT),
            "--log-path",
            str(log_path),
            "--write-step-summary",
        ],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env({"GITHUB_STEP_SUMMARY": str(step_summary)}),
    )
    assert emit_res.returncode == 0, emit_res.stderr
    text = step_summary.read_text(encoding="utf-8")
    assert "### Alert docs gate metrics" in text
    assert "| summary_version |" in text
    assert "| metrics_emit_version |" in text


def test_emit_alert_docs_gate_metrics_ok_via_python_module(tmp_path: Path) -> None:
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
        [sys.executable, "-m", "tbox_pipelines.metrics_emit_cli", "--log-path", str(log_path)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_emit_env(),
    )
    assert emit_res.returncode == 0, emit_res.stderr
    assert emit_res.stdout.startswith(
        "alert_docs_gate_metrics event=alert_docs_gate_ok summary_version=1 metrics_emit_version=1 "
    )
