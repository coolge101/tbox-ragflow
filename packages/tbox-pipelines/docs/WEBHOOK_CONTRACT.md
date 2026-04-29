# TBOX Pipelines Webhook Contract

HTTP `POST` with `Content-Type: application/json`. All envelopes share top-level fields; interpret by `type`.

## Envelope (all types)

| Field | Type | Description |
|-------|------|-------------|
| `payload_version` | int | Envelope schema version (currently `1`). Receivers may branch on this. |
| `type` | string | Discriminator: `tbox_sync_summary` or `tbox_rbac_alert`. |
| `status` | string | Convenience copy of inner primary status (`summary.status` or `rbac.status`). |
| `sync_id` | string | Correlation id for the run (same as inner when present). |

## `tbox_sync_summary` (business sync)

Configured via `notify_webhook_url` / `RAGFLOW_NOTIFY_WEBHOOK_URL`.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | object | Same shape as one line of `sync_audit.jsonl` / `sync_summary` log: e.g. `sync_id`, `status`, `documents_fetched`, `resolved_dataset_id`, `uploaded_doc_ids`, `run_triggered`, `auto_run_after_upload`, optional RBAC policy metadata when present, etc. |

Notification policy: failures always eligible; success only if `notify_on_success` is true.

## `tbox_rbac_alert` (RBAC high-risk)

Configured via `rbac_alert_webhook_url` / `TBOX_RBAC_ALERT_WEBHOOK_URL`. Only sent for high-risk failed RBAC events (see `TBOX_RBAC_ALERT_HIGH_RISK_REASONS`), after dedupe rules.

| Field | Type | Description |
|-------|------|-------------|
| `rbac` | object | RBAC event: `sync_id`, `status`, `reason`, `actor_role`, optional `error`, policy fields (`rbac_policy_source`, `rbac_policy_fingerprint`, `rbac_policy_version`, `rbac_policy_release_tag`), and when applicable `rbac_alert_suppressed_in_window` (count of suppressed alerts since last emit for the same dedupe key). |

## JSON Schema (machine-readable)

Canonical schema (Draft 07 `oneOf` for the two payload shapes):

- [`webhook_payload.schema.json`](webhook_payload.schema.json)

Validate locally (example with [ajv-cli](https://www.npmjs.com/package/ajv-cli)):

```bash
npx ajv-cli validate -s docs/webhook_payload.schema.json -d payload.json
```

## Example payloads and `curl`

### `tbox_sync_summary`

```json
{
  "payload_version": 1,
  "type": "tbox_sync_summary",
  "status": "failed",
  "sync_id": "a1b2c3d4e5f6",
  "summary": {
    "sync_id": "a1b2c3d4e5f6",
    "status": "failed",
    "reason": "dataset_not_resolved",
    "documents_fetched": 0,
    "resolved_dataset_id": "",
    "uploaded_doc_ids": [],
    "run_triggered": false,
    "auto_run_after_upload": true
  }
}
```

```bash
curl -sS -X POST "$RAGFLOW_NOTIFY_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @payload-sync.json
```

### `tbox_rbac_alert`

```json
{
  "payload_version": 1,
  "type": "tbox_rbac_alert",
  "status": "failed",
  "sync_id": "a1b2c3d4e5f6",
  "rbac": {
    "sync_id": "a1b2c3d4e5f6",
    "status": "failed",
    "reason": "permission_denied",
    "actor_role": "viewer",
    "error": "RBAC denied action='sync:run' for role='viewer'.",
    "rbac_policy_source": "builtin:default",
    "rbac_policy_fingerprint": "0123456789abcdef",
    "rbac_policy_version": "",
    "rbac_policy_release_tag": "",
    "rbac_alert_suppressed_in_window": 0
  }
}
```

```bash
curl -sS -X POST "$TBOX_RBAC_ALERT_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @payload-rbac.json
```

## Versioning

- Increment `WEBHOOK_PAYLOAD_VERSION` in `tbox_pipelines/notify.py` when adding required envelope fields or changing meaning of `type` values.
- Prefer additive changes inside `summary` / `rbac` without bumping envelope version when possible.
- When `payload_version` or required envelope keys change, update `webhook_payload.schema.json` and the examples above.
