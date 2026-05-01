from __future__ import annotations

from pathlib import Path

# tests/ -> tbox-pipelines/ -> packages/ -> repo root (tbox-ragflow-platform)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CI_YML = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_yml_alert_docs_gate_workflow_invariant() -> None:
    """Lock CI diagnostics to `doctor` only (see S3.192); keep file readable under sparse-checkout."""
    assert _CI_YML.is_file(), f"expected {_CI_YML}"
    text = _CI_YML.read_text(encoding="utf-8")
    assert text.count("alert-docs-gate doctor") == 2
    assert "alert-docs-gate version" not in text
    assert "alert-docs-gate commands" not in text
