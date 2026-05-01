#!/usr/bin/env python3
"""Emit CI-friendly metrics from validate_alert_docs_links summary logs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_DEFAULT_METRICS_SCHEMA_PATH = str(
    Path(__file__).resolve().parent.parent
    / "docs"
    / "examples"
    / "alert_docs_gate_metrics_payload.schema.json"
)


def _validate_metrics_payload_against_schema(
    payload: dict[str, object],
    schema: object,
) -> None:
    """Subset of Draft-07 checks for the metrics JSON payload (no external deps)."""
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


def _load_emit_settings(rules_path: Path) -> tuple[str, int, tuple[str, ...], int]:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    if not isinstance(rules, dict):
        raise ValueError("rules payload must be a JSON object")
    summary_contract = rules.get("summary_contract")
    if not isinstance(summary_contract, dict):
        raise ValueError("summary_contract must be an object")

    event = summary_contract.get("event")
    if not isinstance(event, str) or not event:
        raise ValueError("summary_contract.event must be a non-empty string")

    summary_version = summary_contract.get("summary_version")
    if (
        not isinstance(summary_version, int)
        or isinstance(summary_version, bool)
        or summary_version < 1
    ):
        raise ValueError("summary_contract.summary_version must be an integer >= 1")

    metric_keys = summary_contract.get("metric_keys")
    if not isinstance(metric_keys, list) or not metric_keys:
        raise ValueError("summary_contract.metric_keys must be a non-empty array")
    if not all(isinstance(key, str) and key for key in metric_keys):
        raise ValueError("summary_contract.metric_keys must contain non-empty strings")
    if len(metric_keys) != len(set(metric_keys)):
        raise ValueError("summary_contract.metric_keys must not contain duplicates")

    metrics_emit_contract = rules.get("metrics_emit_contract")
    if not isinstance(metrics_emit_contract, dict):
        raise ValueError("metrics_emit_contract must be an object")
    emit_version = metrics_emit_contract.get("emit_version")
    if not isinstance(emit_version, int) or isinstance(emit_version, bool) or emit_version < 1:
        raise ValueError("metrics_emit_contract.emit_version must be an integer >= 1")

    return event, summary_version, tuple(metric_keys), emit_version


def _extract_summary_payload(log_path: Path, prefix: str) -> dict[str, object]:
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            payload = json.loads(line[len(prefix) :])
            if not isinstance(payload, dict):
                raise ValueError("summary payload must be a JSON object")
            return payload
    raise ValueError("missing alert docs gate summary line")


def _to_metrics_line(
    payload: dict[str, object],
    *,
    expected_event: str,
    expected_summary_version: int,
    metric_keys: tuple[str, ...],
    metrics_emit_version: int | None = None,
) -> str:
    if payload.get("event") != expected_event:
        raise ValueError(
            f"summary event mismatch: expected {expected_event}, got {payload.get('event')}"
        )
    if payload.get("summary_version") != expected_summary_version:
        raise ValueError(
            "summary version mismatch: "
            f"expected {expected_summary_version}, got {payload.get('summary_version')}"
        )

    expected_keys = {"event", "summary_version", *metric_keys}
    extra_keys = [key for key in payload if key not in expected_keys]
    if extra_keys:
        raise ValueError(f"summary payload has unexpected key(s): {','.join(extra_keys)}")
    missing_keys = [key for key in metric_keys if key not in payload]
    if missing_keys:
        raise ValueError(f"summary payload missing metric key(s): {','.join(missing_keys)}")
    invalid_metric_values: list[str] = []
    for key in metric_keys:
        value = payload[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            invalid_metric_values.append(key)
    if invalid_metric_values:
        raise ValueError(
            "summary payload metric value must be a non-negative integer for key(s): "
            + ",".join(invalid_metric_values)
        )

    parts: list[str] = ["alert_docs_gate_metrics"]
    parts.append(f"event={payload['event']}")
    parts.append(f"summary_version={payload['summary_version']}")
    if metrics_emit_version is not None:
        parts.append(f"metrics_emit_version={metrics_emit_version}")
    for key in metric_keys:
        parts.append(f"{key}={payload[key]}")
    return " ".join(parts)


def _to_metrics_json(
    payload: dict[str, object],
    *,
    metric_keys: tuple[str, ...],
    metrics_emit_version: int,
) -> str:
    metrics_payload = _metrics_payload_dict(
        payload,
        metric_keys=metric_keys,
        metrics_emit_version=metrics_emit_version,
    )
    return "alert_docs_gate_metrics_json " + json.dumps(
        metrics_payload,
        ensure_ascii=True,
        sort_keys=True,
    )


def _metrics_payload_dict(
    payload: dict[str, object],
    *,
    metric_keys: tuple[str, ...],
    metrics_emit_version: int,
) -> dict[str, object]:
    metrics_payload: dict[str, object] = {
        "event": payload["event"],
        "summary_version": payload["summary_version"],
        "metrics_emit_version": metrics_emit_version,
    }
    for key in metric_keys:
        metrics_payload[key] = payload[key]
    return metrics_payload


def _append_github_output(path: Path, name: str, value: str) -> None:
    """Write one GitHub Actions output using heredoc form (safe for JSON)."""
    delimiter = f"EOF_ALERT_DOCS_GATE_{name.upper()}"
    while delimiter in value:
        delimiter = f"{delimiter}_X"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{name}<<{delimiter}\n")
        fh.write(value)
        fh.write(f"\n{delimiter}\n")


def _write_github_outputs(
    *,
    github_output: Path,
    metrics_kv_line: str,
    metrics_json_line: str | None,
    metrics_payload_json: str,
) -> None:
    _append_github_output(github_output, "alert_docs_gate_metrics_kv", metrics_kv_line)
    if metrics_json_line is not None:
        _append_github_output(
            github_output,
            "alert_docs_gate_metrics_json_line",
            metrics_json_line,
        )
    _append_github_output(
        github_output,
        "alert_docs_gate_metrics_json",
        metrics_payload_json,
    )


def _write_step_summary(
    path: Path,
    *,
    metrics_payload: dict[str, object],
    metric_keys: tuple[str, ...],
) -> None:
    """Append a small Markdown table to GitHub Actions step summary."""
    lines = [
        "### Alert docs gate metrics",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| event | `{metrics_payload['event']}` |",
        f"| summary_version | {metrics_payload['summary_version']} |",
        f"| metrics_emit_version | {metrics_payload['metrics_emit_version']} |",
    ]
    for key in metric_keys:
        lines.append(f"| {key} | {metrics_payload[key]} |")
    lines.append("")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse docs gate summary log and emit metrics line",
    )
    parser.add_argument(
        "--log-path",
        default="/tmp/alert_docs_gate.log",
        help="Path to log file produced by validate_alert_docs_links.py",
    )
    parser.add_argument(
        "--summary-prefix",
        default="validate_alert_docs_links.py: summary ",
        help="Prefix used by summary log line",
    )
    parser.add_argument(
        "--rules-path",
        default=str(
            Path(__file__).resolve().parent.parent
            / "docs"
            / "examples"
            / "alert_docs_gate_rules.json"
        ),
        help="Path to docs gate rules json with summary_contract",
    )
    parser.add_argument(
        "--emit-json",
        action="store_true",
        help="Also emit JSON mirror line for machine ingestion",
    )
    parser.add_argument(
        "--write-github-output",
        action="store_true",
        help="Append metrics to GITHUB_OUTPUT when that env var is set (CI)",
    )
    parser.add_argument(
        "--write-step-summary",
        action="store_true",
        help="Append metrics Markdown to GITHUB_STEP_SUMMARY when that env var is set (CI)",
    )
    parser.add_argument(
        "--metrics-schema-path",
        default=_DEFAULT_METRICS_SCHEMA_PATH,
        help="JSON Schema path for metrics payload validation",
    )
    args = parser.parse_args()

    try:
        event, summary_version, metric_keys, metrics_emit_version = _load_emit_settings(
            Path(args.rules_path)
        )
        summary_payload = _extract_summary_payload(
            log_path=Path(args.log_path),
            prefix=args.summary_prefix,
        )
        metrics_line = _to_metrics_line(
            summary_payload,
            expected_event=event,
            expected_summary_version=summary_version,
            metric_keys=metric_keys,
            metrics_emit_version=metrics_emit_version,
        )
        metrics_payload = _metrics_payload_dict(
            summary_payload,
            metric_keys=metric_keys,
            metrics_emit_version=metrics_emit_version,
        )
        metrics_schema_path = Path(
            os.environ.get(
                "ALERT_DOCS_GATE_METRICS_SCHEMA_PATH",
                args.metrics_schema_path,
            )
        )
        metrics_schema = json.loads(metrics_schema_path.read_text(encoding="utf-8"))
        _validate_metrics_payload_against_schema(metrics_payload, metrics_schema)
        metrics_payload_json = json.dumps(
            metrics_payload,
            ensure_ascii=True,
            sort_keys=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    print(metrics_line)
    json_line: str | None = None
    if args.emit_json:
        json_line = _to_metrics_json(
            summary_payload,
            metric_keys=metric_keys,
            metrics_emit_version=metrics_emit_version,
        )
        print(json_line)

    if args.write_github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if out_path:
            _write_github_outputs(
                github_output=Path(out_path),
                metrics_kv_line=metrics_line,
                metrics_json_line=json_line,
                metrics_payload_json=metrics_payload_json,
            )

    if args.write_step_summary:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            _write_step_summary(
                Path(summary_path),
                metrics_payload=metrics_payload,
                metric_keys=metric_keys,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
