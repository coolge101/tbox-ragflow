from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "validate_alert_docs_links.py"
_RULES = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.json"
_RULES_SCHEMA = _ROOT / "docs" / "examples" / "alert_docs_gate_rules.schema.json"


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
    assert "ok all required doc links present" in res.stdout
