from __future__ import annotations

import json
from pathlib import Path

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "sync:run",
        "dataset:auto_create",
        "source:http_json",
        "ragflow:run_documents",
    },
    "ingest_bot": {
        "sync:run",
        "dataset:auto_create",
        "source:http_json",
        "ragflow:run_documents",
    },
    "operator": {
        "sync:run",
        "source:http_json",
        "ragflow:run_documents",
    },
    "viewer": set(),
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    role: set(actions) for role, actions in DEFAULT_ROLE_PERMISSIONS.items()
}


def normalize_role(role: str) -> str:
    return role.strip().lower() if role else "ingest_bot"


def is_allowed(role: str, action: str) -> bool:
    role_name = normalize_role(role)
    return action in ROLE_PERMISSIONS.get(role_name, set())


def require_permission(role: str, action: str) -> None:
    if is_allowed(role, action):
        return
    raise PermissionError(
        f"RBAC denied action={action!r} for role={normalize_role(role)!r}. "
        "Check TBOX_ACTOR_ROLE or permission matrix."
    )


def configure_policy(policy: dict[str, list[str] | set[str] | tuple[str, ...]]) -> None:
    loaded: dict[str, set[str]] = {}
    for role, actions in policy.items():
        role_name = normalize_role(role)
        loaded[role_name] = {str(action).strip() for action in actions if str(action).strip()}
    ROLE_PERMISSIONS.clear()
    ROLE_PERMISSIONS.update(loaded)


def configure_policy_from_file(path: str) -> bool:
    if not path:
        return False
    target = Path(path)
    if not target.exists():
        raise ValueError(f"RBAC policy file not found: {path}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RBAC policy file must be a role->actions JSON object")
    configure_policy(payload)
    return True


def reset_default_policy() -> None:
    ROLE_PERMISSIONS.clear()
    ROLE_PERMISSIONS.update(
        {role: set(actions) for role, actions in DEFAULT_ROLE_PERMISSIONS.items()}
    )
