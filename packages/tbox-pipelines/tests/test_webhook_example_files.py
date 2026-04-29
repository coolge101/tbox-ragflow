from __future__ import annotations

import json
from pathlib import Path

import pytest

from tbox_pipelines.notify import WEBHOOK_PAYLOAD_VERSION

# Must match schema oneOf / definitions for payload shapes (not envelope).
_WEBHOOK_PAYLOAD_TYPES = frozenset({"tbox_sync_summary", "tbox_rbac_alert"})

_DOCS = Path(__file__).resolve().parent.parent / "docs"
_DOCS_EXAMPLES = _DOCS / "examples"
_SCHEMA_PATH = _DOCS / "webhook_payload.schema.json"


def _sample_json_paths() -> list[Path]:
    return sorted(_DOCS_EXAMPLES.glob("*.sample.json"))


def test_webhook_payload_schema_parses() -> None:
    data = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("$schema") == "http://json-schema.org/draft-07/schema#"
    one_of = data.get("oneOf")
    assert isinstance(one_of, list) and len(one_of) == 2
    defs = data.get("definitions")
    assert isinstance(defs, dict)
    assert "envelope" in defs
    assert "tbox_sync_summary" in defs
    assert "tbox_rbac_alert" in defs
    refs = {item.get("$ref") for item in one_of if isinstance(item, dict)}
    assert refs == {f"#/definitions/{t}" for t in _WEBHOOK_PAYLOAD_TYPES}


def test_webhook_example_samples_exist() -> None:
    assert _sample_json_paths(), "expected docs/examples/*.sample.json for webhook contract smoke"


def test_webhook_example_samples_cover_all_payload_types() -> None:
    types_from_names = {p.name.removesuffix(".sample.json") for p in _sample_json_paths()}
    assert types_from_names == _WEBHOOK_PAYLOAD_TYPES


@pytest.mark.parametrize("path", _sample_json_paths(), ids=lambda p: p.name)
def test_webhook_example_envelope_smoke(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.name.endswith(".sample.json")
    expected_type = path.name.removesuffix(".sample.json")
    assert expected_type
    assert data.get("payload_version") == WEBHOOK_PAYLOAD_VERSION
    ptype = data.get("type")
    assert ptype == expected_type
    assert ptype in _WEBHOOK_PAYLOAD_TYPES
    assert isinstance(data.get("status"), str)
    assert isinstance(data.get("sync_id"), str)
    if ptype == "tbox_sync_summary":
        inner = data.get("summary")
        assert isinstance(inner, dict)
        assert inner.get("sync_id") == data.get("sync_id")
        assert data.get("status") == inner.get("status", "unknown")
    else:
        inner = data.get("rbac")
        assert isinstance(inner, dict)
        assert inner.get("sync_id") == data.get("sync_id")
        assert data.get("status") == inner.get("status", "unknown")
