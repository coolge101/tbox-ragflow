#!/usr/bin/env bash
# Validate checked-in webhook example payloads against docs/webhook_payload.schema.json.
# Same checks as CI (.github/workflows/ci.yml). Run from repo: packages/tbox-pipelines.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! command -v node >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: node is required (CI uses Node 20; see .node-version)." >&2
  exit 1
fi
npx --yes ajv-cli validate -s docs/webhook_payload.schema.json -d docs/examples/tbox_sync_summary.sample.json
npx --yes ajv-cli validate -s docs/webhook_payload.schema.json -d docs/examples/tbox_rbac_alert.sample.json
