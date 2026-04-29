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

Validate locally (requires Node/npm; uses [ajv-cli](https://www.npmjs.com/package/ajv-cli) via `npx --yes`). Use Node **20** to match CI (this package ships [`.node-version`](../.node-version) for nvm/fnm/volta). From `packages/tbox-pipelines`:

```bash
bash scripts/validate_webhook_examples.sh
```

### CI

The `tbox-pipelines` GitHub Actions job runs `bash scripts/validate_webhook_examples.sh` (Node 20). See `.github/workflows/ci.yml` at the repository root. If you change `webhook_payload.schema.json` or the files under `docs/examples/`, keep them in sync or CI will fail.

## Example payload files

Checked-in copies you can send or validate as-is:

| File | `type` |
|------|--------|
| [`examples/tbox_sync_summary.sample.json`](examples/tbox_sync_summary.sample.json) | `tbox_sync_summary` |
| [`examples/tbox_rbac_alert.sample.json`](examples/tbox_rbac_alert.sample.json) | `tbox_rbac_alert` |

## Example `curl` (from `packages/tbox-pipelines`)

### `tbox_sync_summary`

```bash
curl -sS -X POST "$RAGFLOW_NOTIFY_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @docs/examples/tbox_sync_summary.sample.json
```

### `tbox_rbac_alert`

```bash
curl -sS -X POST "$TBOX_RBAC_ALERT_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @docs/examples/tbox_rbac_alert.sample.json
```

## Versioning

- Increment `WEBHOOK_PAYLOAD_VERSION` in `tbox_pipelines/notify.py` when adding required envelope fields or changing meaning of `type` values.
- Prefer additive changes inside `summary` / `rbac` without bumping envelope version when possible.
- When `payload_version` or required envelope keys change, update `webhook_payload.schema.json` and the files under `docs/examples/`.
