from __future__ import annotations

import json

import pytest

from tbox_pipelines.rbac import (
    configure_policy_from_file,
    is_allowed,
    require_permission,
    reset_default_policy,
)


def test_ingest_bot_can_run_sync() -> None:
    assert is_allowed("ingest_bot", "sync:run")
    require_permission("ingest_bot", "sync:run")


def test_viewer_cannot_run_sync() -> None:
    assert not is_allowed("viewer", "sync:run")
    with pytest.raises(PermissionError):
        require_permission("viewer", "sync:run")


def test_configure_policy_from_file(tmp_path) -> None:
    policy_path = tmp_path / "rbac.json"
    policy_path.write_text(
        json.dumps(
            {
                "viewer": ["sync:run"],
                "ingest_bot": [],
            }
        ),
        encoding="utf-8",
    )

    try:
        loaded = configure_policy_from_file(str(policy_path))
        assert loaded
        assert is_allowed("viewer", "sync:run")
        assert not is_allowed("ingest_bot", "sync:run")
    finally:
        reset_default_policy()
