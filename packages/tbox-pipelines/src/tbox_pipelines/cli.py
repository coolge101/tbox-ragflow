from __future__ import annotations

import argparse
import logging

import httpx

from tbox_pipelines.workflows.sync_job import SyncConfigError, run_sync

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_CONFIG_ERROR = 2
EXIT_REMOTE_ERROR = 3
EXIT_UNKNOWN_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TBOX pipeline scaffold CLI")
    parser.add_argument("command", choices=["sync"], help="Command to execute")
    parser.add_argument(
        "--config",
        default=None,
        help="Optional config json path (default: config/pipeline.sample.json)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "sync":
            count = run_sync(config_path=args.config)
            print(f"sync finished, documents={count}")
        return EXIT_OK
    except SyncConfigError as exc:
        logger.error("sync_config_error: %s", exc)
        return EXIT_CONFIG_ERROR
    except httpx.HTTPError as exc:
        logger.error("sync_remote_error: %s", exc)
        return EXIT_REMOTE_ERROR
    except Exception as exc:  # noqa: BLE001
        logger.exception("sync_unknown_error: %s", exc)
        return EXIT_UNKNOWN_ERROR
