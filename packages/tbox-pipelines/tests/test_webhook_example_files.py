from __future__ import annotations

import json
from pathlib import Path

import pytest

from tbox_pipelines.notify import WEBHOOK_PAYLOAD_VERSION

_DOCS = Path(__file__).resolve().parent.parent / "docs"
_DOCS_EXAMPLES = _DOCS / "examples"
_SCHEMA_PATH = _DOCS / "webhook_payload.schema.json"
_SCHEMA_DATA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _webhook_payload_types_from_schema_data(data: dict) -> frozenset[str]:
    """Payload `type` values from schema root `oneOf` (`#/definitions/<name>` refs)."""
    one_of = data.get("oneOf")
    if not isinstance(one_of, list):
        return frozenset()
    names: set[str] = set()
    for item in one_of:
        if not isinstance(item, dict):
            continue
        ref = item.get("$ref")
        if not isinstance(ref, str) or not ref.startswith("#/definitions/"):
            continue
        names.add(ref.removeprefix("#/definitions/"))
    return frozenset(names)


_WEBHOOK_PAYLOAD_TYPES = _webhook_payload_types_from_schema_data(_SCHEMA_DATA)


def _inner_payload_key_for_type(typename: str) -> str:
    """Nested object key (e.g. summary, rbac) from definitions.<t>.allOf[].required."""
    defs = _SCHEMA_DATA.get("definitions")
    if not isinstance(defs, dict):
        msg = "schema definitions missing"
        raise AssertionError(msg)
    d = defs.get(typename)
    if not isinstance(d, dict):
        msg = f"schema definitions missing {typename!r}"
        raise AssertionError(msg)
    keys: list[str] = []
    for part in d.get("allOf", []):
        if not isinstance(part, dict):
            continue
        req = part.get("required")
        if not isinstance(req, list):
            continue
        for k in req:
            if k != "type":
                keys.append(k)
    uniq: list[str] = []
    seen: set[str] = set()
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    if len(uniq) != 1:
        msg = "expected one non-type body key in allOf.required for "
        msg += f"{typename!r}, got {uniq!r}"
        raise AssertionError(msg)
    return uniq[0]


def _type_const_from_definition(typename: str) -> str | None:
    """`properties.type.const` from definitions.<typename> allOf (if present)."""
    defs = _SCHEMA_DATA.get("definitions")
    if not isinstance(defs, dict):
        return None
    d = defs.get(typename)
    if not isinstance(d, dict):
        return None
    for part in d.get("allOf", []):
        if not isinstance(part, dict):
            continue
        props = part.get("properties")
        if not isinstance(props, dict):
            continue
        tspec = props.get("type")
        if isinstance(tspec, dict) and "const" in tspec:
            c = tspec.get("const")
            if isinstance(c, str):
                return c
    return None


def _sample_json_paths() -> list[Path]:
    return sorted(_DOCS_EXAMPLES.glob("*.sample.json"))


def test_webhook_payload_schema_parses() -> None:
    assert len(_WEBHOOK_PAYLOAD_TYPES) >= 2
    data = _SCHEMA_DATA
    assert isinstance(data, dict)
    assert data.get("$schema") == "http://json-schema.org/draft-07/schema#"
    one_of = data.get("oneOf")
    assert isinstance(one_of, list) and len(one_of) == len(_WEBHOOK_PAYLOAD_TYPES)
    defs = data.get("definitions")
    assert isinstance(defs, dict)
    assert "envelope" in defs
    for t in _WEBHOOK_PAYLOAD_TYPES:
        assert t in defs
    refs = {item.get("$ref") for item in one_of if isinstance(item, dict)}
    assert refs == {f"#/definitions/{t}" for t in _WEBHOOK_PAYLOAD_TYPES}


def test_webhook_payload_schema_type_const_matches_definition() -> None:
    for t in _WEBHOOK_PAYLOAD_TYPES:
        const = _type_const_from_definition(t)
        assert const == t, f"definitions.{t} properties.type.const should be {t!r}, got {const!r}"


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
    assert data["status"], "sample envelope status should be non-empty"
    assert isinstance(data.get("sync_id"), str)
    body_key = _inner_payload_key_for_type(ptype)
    for k in ("payload_version", "type", "status", "sync_id", body_key):
        assert k in data
    expected_top_level = {"payload_version", "type", "status", "sync_id", body_key}
    assert set(data) == expected_top_level
    assert data["sync_id"], "sample envelope sync_id should be non-empty"
    disallowed = _WEBHOOK_PAYLOAD_TYPES - {ptype}
    for other in disallowed:
        other_key = _inner_payload_key_for_type(other)
        assert other_key not in data
    inner = data[body_key]
    assert isinstance(inner, dict)
    assert "status" in inner
    assert isinstance(inner["status"], str)
    assert inner["status"], "sample inner status should be non-empty"
    assert "sync_id" in inner
    assert isinstance(inner["sync_id"], str)
    assert inner["sync_id"] == data["sync_id"]
    assert inner["sync_id"], "sample inner sync_id should be non-empty"
    assert data.get("status") == inner.get("status", "unknown")
