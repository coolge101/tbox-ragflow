#!/usr/bin/env python3
"""Validate a docs-gate metrics JSON payload against alert_docs_gate_metrics_payload.schema.json."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from tbox_pipelines.metrics_payload_validate_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
