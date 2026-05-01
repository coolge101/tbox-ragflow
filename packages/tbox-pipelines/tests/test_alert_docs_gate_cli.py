from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


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
