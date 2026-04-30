from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "validate_alert_docs_links.py"
_RULES = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.json"
_RULES_SCHEMA = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.schema.json"
_INVALID_RULES_DIR = _ROOT / "docs" / "examples" / "gate_rules_invalid"


def test_validate_alert_docs_links_rules_file_is_valid_json() -> None:
    data = json.loads(_RULES.read_text(encoding="utf-8"))
    schema = json.loads(_RULES_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("type") == "object"
    assert isinstance(data.get("required_example_files"), list)
    assert isinstance(data.get("required_changelog_stage_tokens"), list)
    assert isinstance(data.get("examples_readme_required_tokens"), list)


def test_validate_alert_docs_links_script_passes() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "summary {" in res.stdout
    assert '"event": "alert_docs_gate_ok"' in res.stdout
    assert "ok all required doc links present" in res.stdout


def test_validate_alert_docs_links_script_verbose_mode() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "--verbose"],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "verbose rules_loaded" in res.stdout
    assert "verbose check_summary" in res.stdout
    assert "ok all required doc links present" in res.stdout


def test_validate_alert_docs_links_invalid_rules_samples_fail() -> None:
    bad_cases = (
        (
            "missing_required_example_files.json",
            "rules missing required key: required_example_files",
        ),
        ("bad_stage_pattern.json", "required_changelog_stage_tokens[1].stage is invalid"),
        (
            "empty_evidence_tokens.json",
            "required_changelog_stage_tokens[1].evidence_tokens must be non-empty array",
        ),
    )
    for filename, expected_error in bad_cases:
        env = dict(**os.environ)
        env["ALERT_DOCS_GATE_RULES_PATH"] = str(_INVALID_RULES_DIR / filename)
        env["ALERT_DOCS_GATE_SCHEMA_PATH"] = str(_RULES_SCHEMA)
        res = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        assert res.returncode != 0, f"{filename} should fail validation"
        assert "fail total_errors=" in res.stderr
        assert expected_error in res.stderr
