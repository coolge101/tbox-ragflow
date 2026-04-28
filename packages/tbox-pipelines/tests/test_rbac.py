from __future__ import annotations

import pytest

from tbox_pipelines.rbac import is_allowed, require_permission


def test_ingest_bot_can_run_sync() -> None:
    assert is_allowed("ingest_bot", "sync:run")
    require_permission("ingest_bot", "sync:run")


def test_viewer_cannot_run_sync() -> None:
    assert not is_allowed("viewer", "sync:run")
    with pytest.raises(PermissionError):
        require_permission("viewer", "sync:run")
