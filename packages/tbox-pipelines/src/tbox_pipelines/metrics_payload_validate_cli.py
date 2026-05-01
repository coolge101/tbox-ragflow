"""CLI: validate alert-docs gate metrics JSON against the metrics payload JSON Schema."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from tbox_pipelines.alert_docs_gate_metrics_schema import (
    DEFAULT_METRICS_SCHEMA_PATH,
    validate_metrics_payload_against_schema,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate metrics JSON (stdin or --payload-path) against schema",
    )
    parser.add_argument(
        "--schema-path",
        default=os.environ.get(
            "ALERT_DOCS_GATE_METRICS_SCHEMA_PATH",
            DEFAULT_METRICS_SCHEMA_PATH,
        ),
        help="Path to metrics payload JSON Schema",
    )
    parser.add_argument(
        "--payload-path",
        default="",
        help="Path to JSON payload file (default: read stdin)",
    )
    args = parser.parse_args()

    raw = (
        Path(args.payload_path).read_text(encoding="utf-8")
        if args.payload_path
        else sys.stdin.read()
    )
    if not raw.strip():
        print("empty payload", file=sys.stderr)
        return 1
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        print("payload must be a JSON object", file=sys.stderr)
        return 1
    schema = json.loads(Path(args.schema_path).read_text(encoding="utf-8"))
    try:
        validate_metrics_payload_against_schema(payload, schema)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("validate_alert_docs_metrics_payload.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
