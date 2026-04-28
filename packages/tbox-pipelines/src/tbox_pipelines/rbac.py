from __future__ import annotations

ROLE_PERMISSIONS: dict[str, set[str]] = {
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
