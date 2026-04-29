from __future__ import annotations

import json
from pathlib import Path

import pytest

from tbox_pipelines.notify import WEBHOOK_PAYLOAD_VERSION

_DOCS = Path(__file__).resolve().parent.parent / "docs"
_DOCS_EXAMPLES = _DOCS / "examples"
_SCHEMA_PATH = _DOCS / "webhook_payload.schema.json"


def _sample_json_paths() -> list[Path]:
    return sorted(_DOCS_EXAMPLES.glob("*.sample.json"))


def test_webhook_payload_schema_parses() -> None:
    data = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("$schema") == "http://json-schema.org/draft-07/schema#"
    assert isinstance(data.get("oneOf"), list)
    assert isinstance(data.get("definitions"), dict)


def test_webhook_example_samples_exist() -> None:
    assert _sample_json_paths(), "expected docs/examples/*.sample.json for webhook contract smoke"


@pytest.mark.parametrize("path", _sample_json_paths(), ids=lambda p: p.name)
def test_webhook_example_envelope_smoke(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("payload_version") == WEBHOOK_PAYLOAD_VERSION
    ptype = data.get("type")
    assert ptype in ("tbox_sync_summary", "tbox_rbac_alert")
    assert isinstance(data.get("status"), str)
    assert isinstance(data.get("sync_id"), str)
    if ptype == "tbox_sync_summary":
        assert isinstance(data.get("summary"), dict)
    else:
        assert isinstance(data.get("rbac"), dict)
