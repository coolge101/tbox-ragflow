#!/usr/bin/env python3
"""Emit CI-friendly metrics from validate_alert_docs_links summary logs."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from tbox_pipelines.metrics_emit_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
