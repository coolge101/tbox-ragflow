"""Unified CLI for alert-docs gate: validate links, metrics payload, emit, and CI bundle."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from tbox_pipelines import (
    alert_docs_links_validate_cli,
    metrics_emit_cli,
    metrics_payload_validate_cli,
)
from tbox_pipelines.alert_docs_gate_metrics_schema import DEFAULT_METRICS_SCHEMA_PATH


class _TeeStdout:
    """Mirror text written to stdout into a second stream (e.g. log file)."""

    __slots__ = ("_primary", "_secondary", "encoding")

    def __init__(self, primary: object, secondary: object) -> None:
        self._primary = primary
        self._secondary = secondary
        self.encoding = getattr(primary, "encoding", None) or "utf-8"

    def write(self, data: str) -> int:
        self._primary.write(data)
        self._secondary.write(data)
        self._primary.flush()
        self._secondary.flush()
        return len(data)

    def flush(self) -> None:
        self._primary.flush()
        self._secondary.flush()

    def isatty(self) -> bool:
        isatty = getattr(self._primary, "isatty", None)
        return bool(isatty()) if callable(isatty) else False


def _run_metrics_validate(*, schema_path: str, payload_path: str) -> int:
    prev = sys.argv
    argv = ["validate-alert-docs-metrics-payload", "--schema-path", schema_path]
    if payload_path:
        argv.extend(["--payload-path", payload_path])
    sys.argv = argv
    try:
        return metrics_payload_validate_cli.main()
    finally:
        sys.argv = prev


def _run_validate_only(*, verbose: bool) -> int:
    prev = sys.argv
    sys.argv = ["validate-alert-docs-links", *([] if not verbose else ["--verbose"])]
    try:
        return alert_docs_links_validate_cli.main()
    finally:
        sys.argv = prev


def _run_ci(
    *,
    verbose: bool,
    log_path: Path,
    emit_json: bool,
    write_github_output: bool,
    write_step_summary: bool,
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    prev_argv = sys.argv
    prev_stdout = sys.stdout
    with log_path.open("w", encoding="utf-8") as logf:
        sys.stdout = _TeeStdout(prev_stdout, logf)
        try:
            sys.argv = ["validate-alert-docs-links", *([] if not verbose else ["--verbose"])]
            rv = alert_docs_links_validate_cli.main()
        finally:
            sys.stdout = prev_stdout
            sys.argv = prev_argv
    if rv != 0:
        return rv

    emit_argv = [
        "emit-alert-docs-gate-metrics",
        "--log-path",
        str(log_path),
    ]
    if emit_json:
        emit_argv.append("--emit-json")
    if write_github_output:
        emit_argv.append("--write-github-output")
    if write_step_summary:
        emit_argv.append("--write-step-summary")
    sys.argv = emit_argv
    try:
        return metrics_emit_cli.main()
    finally:
        sys.argv = prev_argv


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="alert-docs-gate",
        description="Alert docs gate: link validation, metrics payload checks, and emission",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ci = sub.add_parser(
        "ci",
        help="Validate links (stdout + tee to log), then emit metrics (CI bundle)",
    )
    p_ci.add_argument("--verbose", action="store_true")
    p_ci.add_argument(
        "--log-path",
        default="/tmp/alert_docs_gate.log",
        help="Log file path (validate output mirror for emit)",
    )
    p_ci.add_argument("--emit-json", action="store_true")
    p_ci.add_argument("--write-github-output", action="store_true")
    p_ci.add_argument("--write-step-summary", action="store_true")

    p_val = sub.add_parser(
        "validate",
        help="Same as validate-alert-docs-links (standalone)",
    )
    p_val.add_argument("--verbose", action="store_true")

    p_mv = sub.add_parser(
        "metrics-validate",
        help="Same as validate-alert-docs-metrics-payload (stdin or --payload-path)",
    )
    p_mv.add_argument(
        "--schema-path",
        default=os.environ.get(
            "ALERT_DOCS_GATE_METRICS_SCHEMA_PATH",
            DEFAULT_METRICS_SCHEMA_PATH,
        ),
        help="Path to metrics payload JSON Schema",
    )
    p_mv.add_argument(
        "--payload-path",
        default="",
        help="Path to JSON payload file (default: read stdin)",
    )

    args = parser.parse_args()
    if args.command == "ci":
        return _run_ci(
            verbose=args.verbose,
            log_path=Path(args.log_path),
            emit_json=args.emit_json,
            write_github_output=args.write_github_output,
            write_step_summary=args.write_step_summary,
        )
    if args.command == "validate":
        return _run_validate_only(verbose=args.verbose)
    if args.command == "metrics-validate":
        return _run_metrics_validate(
            schema_path=str(args.schema_path),
            payload_path=str(args.payload_path),
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
