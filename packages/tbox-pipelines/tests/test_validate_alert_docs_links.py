from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "validate_alert_docs_links.py"


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
