from __future__ import annotations

import argparse

from tbox_pipelines.workflows.sync_job import run_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TBOX pipeline scaffold CLI")
    parser.add_argument("command", choices=["sync"], help="Command to execute")
    parser.add_argument(
        "--config",
        default=None,
        help="Optional config json path (default: config/pipeline.sample.json)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "sync":
        count = run_sync(config_path=args.config)
        print(f"sync finished, documents={count}")
