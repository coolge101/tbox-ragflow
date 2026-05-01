"""Shared Draft-07 subset validation for alert-docs gate CI metrics JSON payloads."""

from __future__ import annotations

import json
from pathlib import Path

# tbox_pipelines/ -> src/ -> package root (packages/tbox-pipelines)
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_METRICS_SCHEMA_PATH = str(
    PACKAGE_ROOT / "docs" / "examples" / "alert_docs_gate_metrics_payload.schema.json"
)


def validate_metrics_payload_against_schema(
    payload: dict[str, object],
    schema: object,
) -> None:
    """Subset of Draft-07 checks (no jsonschema dependency)."""
    if not isinstance(schema, dict):
        raise ValueError("metrics payload schema must be a JSON object")
    if schema.get("type") != "object":
        raise ValueError("metrics payload schema root type must be object")

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("metrics payload schema properties must be an object")

    additional = schema.get("additionalProperties")
    if additional is False:
        for key in payload:
            if key not in properties:
                raise ValueError(f"metrics payload unexpected key: {key}")

    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in payload:
                raise ValueError(f"metrics payload missing required key: {key}")

    for key, spec in properties.items():
        if key not in payload:
            continue
        if not isinstance(spec, dict):
            continue
        value = payload[key]
        const_val = spec.get("const")
        if const_val is not None and value != const_val:
            raise ValueError(
                f"metrics payload {key} must equal {json.dumps(const_val, ensure_ascii=True)}"
            )
        if const_val is not None:
            continue
        stype = spec.get("type")
        if stype == "string":
            if not isinstance(value, str) or not value:
                raise ValueError(f"metrics payload {key} must be a non-empty string")
        elif stype == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"metrics payload {key} must be an integer")
            minimum = spec.get("minimum")
            if isinstance(minimum, int) and value < minimum:
                raise ValueError(f"metrics payload {key} must be >= {minimum}")
