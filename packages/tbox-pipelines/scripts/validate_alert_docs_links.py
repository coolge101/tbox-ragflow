#!/usr/bin/env python3
"""Validate cross-links for webhook alerting docs examples."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from tbox_pipelines.alert_docs_links_validate_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
