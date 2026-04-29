#!/usr/bin/env bash
# Validate checked-in webhook example payloads against docs/webhook_payload.schema.json.
# Same checks as CI (.github/workflows/ci.yml). Run from repo: packages/tbox-pipelines.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
npx --yes ajv-cli validate -s docs/webhook_payload.schema.json -d docs/examples/tbox_sync_summary.sample.json
npx --yes ajv-cli validate -s docs/webhook_payload.schema.json -d docs/examples/tbox_rbac_alert.sample.json
