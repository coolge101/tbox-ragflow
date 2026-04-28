from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def append_audit_record(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_rbac_audit_record(path: str, payload: dict[str, Any]) -> None:
    append_audit_record(path, payload)
