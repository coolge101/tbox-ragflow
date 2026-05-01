"""Unified CLI for alert-docs gate (subcommands share `_invoke_cli_argv` for argv handoff)."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import sys
from collections.abc import Callable
from pathlib import Path

from tbox_pipelines import (
    alert_docs_links_validate_cli,
    metrics_emit_cli,
    metrics_payload_validate_cli,
)
from tbox_pipelines.alert_docs_gate_metrics_schema import DEFAULT_METRICS_SCHEMA_PATH

_COMMANDS_LINE = (
    "alert-docs-gate commands: ci validate metrics-validate version (emit=pre-argparse forward)"
)


def _invoke_cli_argv(main: Callable[[], int], argv: list[str]) -> int:
    """Run ``main()`` with ``sys.argv`` set to *argv*, then restore prior argv."""
    prev = sys.argv
    sys.argv = argv
    try:
        return main()
    finally:
        sys.argv = prev


def _invoke_emit_cli(emit_args: list[str]) -> int:
    """Run metrics_emit_cli with argv ``emit-alert-docs-gate-metrics`` + emit_args."""
    return _invoke_cli_argv(
        metrics_emit_cli.main,
        ["emit-alert-docs-gate-metrics", *emit_args],
    )


def _argv_tail_after_invocation(argv: list[str]) -> list[str]:
    """Strip interpreter / -m module prefix so tail[0] is the gate subcommand."""
    if len(argv) >= 3 and argv[1] == "-m":
        return list(argv[3:])
    return list(argv[1:])


def _try_emit_forward() -> int | None:
    """If argv is `... emit [EMIT_ARGS...]`, forward to metrics_emit_cli; else None."""
    tail = _argv_tail_after_invocation(sys.argv)
    if len(tail) < 1 or tail[0] != "emit":
        return None
    return _invoke_emit_cli(tail[1:])


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
    argv = ["validate-alert-docs-metrics-payload", "--schema-path", schema_path]
    if payload_path:
        argv.extend(["--payload-path", payload_path])
    return _invoke_cli_argv(metrics_payload_validate_cli.main, argv)


def _run_commands_list() -> int:
    print(_COMMANDS_LINE)
    return 0


def _run_version_print() -> int:
    try:
        print(importlib.metadata.version("tbox-pipelines"))
    except importlib.metadata.PackageNotFoundError:
        print("0.0.0", file=sys.stderr)
        return 1
    return 0


def _run_validate_only(*, verbose: bool) -> int:
    return _invoke_cli_argv(
        alert_docs_links_validate_cli.main,
        ["validate-alert-docs-links", *([] if not verbose else ["--verbose"])],
    )


def _run_ci(
    *,
    verbose: bool,
    log_path: Path,
    emit_json: bool,
    write_github_output: bool,
    write_step_summary: bool,
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    prev_stdout = sys.stdout
    with log_path.open("w", encoding="utf-8") as logf:
        sys.stdout = _TeeStdout(prev_stdout, logf)
        try:
            rv = _invoke_cli_argv(
                alert_docs_links_validate_cli.main,
                ["validate-alert-docs-links", *([] if not verbose else ["--verbose"])],
            )
        finally:
            sys.stdout = prev_stdout
    if rv != 0:
        return rv

    emit_args: list[str] = ["--log-path", str(log_path)]
    if emit_json:
        emit_args.append("--emit-json")
    if write_github_output:
        emit_args.append("--write-github-output")
    if write_step_summary:
        emit_args.append("--write-step-summary")
    return _invoke_emit_cli(emit_args)


def main() -> int:
    emit_rv = _try_emit_forward()
    if emit_rv is not None:
        return emit_rv

    parser = argparse.ArgumentParser(
        prog="alert-docs-gate",
        description="Alert docs gate: link validation, metrics payload checks, and emission",
        epilog=(
            "Emit: `alert-docs-gate emit ...` forwards argv to emit-alert-docs-gate-metrics "
            "(pre-argparse). Use `commands` to list argparse subcommands."
        ),
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

    sub.add_parser(
        "version",
        help="Print tbox-pipelines distribution version (importlib.metadata)",
    )

    sub.add_parser(
        "commands",
        help="Print known subcommand names (emit is pre-argparse; see epilog)",
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
    if args.command == "version":
        return _run_version_print()
    if args.command == "commands":
        return _run_commands_list()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
