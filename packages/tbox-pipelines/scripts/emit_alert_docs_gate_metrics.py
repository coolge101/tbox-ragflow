#!/usr/bin/env python3
"""Emit CI-friendly metrics from validate_alert_docs_links summary logs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _extract_summary_payload(log_path: Path, prefix: str) -> dict[str, object]:
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            payload = json.loads(line[len(prefix) :])
            if not isinstance(payload, dict):
                raise ValueError("summary payload must be a JSON object")
            return payload
    raise ValueError("missing alert docs gate summary line")


def _to_metrics_line(payload: dict[str, object]) -> str:
    parts: list[str] = ["alert_docs_gate_metrics"]
    if "event" in payload:
        parts.append(f"event={payload['event']}")
    if "summary_version" in payload:
        parts.append(f"summary_version={payload['summary_version']}")
    for key, value in payload.items():
        if key in {"event", "summary_version"}:
            continue
        parts.append(f"{key}={value}")
    return " ".join(parts)


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
    args = parser.parse_args()

    try:
        summary_payload = _extract_summary_payload(
            log_path=Path(args.log_path),
            prefix=args.summary_prefix,
        )
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    print(_to_metrics_line(summary_payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
