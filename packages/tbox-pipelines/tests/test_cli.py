from __future__ import annotations

import httpx
import pytest

from tbox_pipelines import cli
from tbox_pipelines.workflows.sync_job import SyncConfigError


def test_cli_returns_success_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["prog", "sync"])
    monkeypatch.setattr("tbox_pipelines.cli.run_sync", lambda config_path=None: 1)

    assert cli.main() == cli.EXIT_OK


def test_cli_returns_config_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["prog", "sync"])

    def _raise_config(*, config_path=None):
        raise SyncConfigError("x")

    monkeypatch.setattr("tbox_pipelines.cli.run_sync", _raise_config)
    assert cli.main() == cli.EXIT_CONFIG_ERROR


def test_cli_returns_remote_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["prog", "sync"])

    def _raise_remote(*, config_path=None):
        raise httpx.ConnectError("x")

    monkeypatch.setattr("tbox_pipelines.cli.run_sync", _raise_remote)
    assert cli.main() == cli.EXIT_REMOTE_ERROR


def test_cli_returns_unknown_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["prog", "sync"])

    def _raise_unknown(*, config_path=None):
        raise RuntimeError("x")

    monkeypatch.setattr("tbox_pipelines.cli.run_sync", _raise_unknown)
    assert cli.main() == cli.EXIT_UNKNOWN_ERROR
