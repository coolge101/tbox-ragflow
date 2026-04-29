#!/usr/bin/env bash
# Validate every docs/examples/*.sample.json against docs/webhook_payload.schema.json.
# Same checks as CI (.github/workflows/ci.yml). Run from repo: packages/tbox-pipelines.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! command -v node >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: node is required (CI uses Node 20; see .node-version)." >&2
  exit 1
fi
shopt -s nullglob
samples=(docs/examples/*.sample.json)
if ((${#samples[@]} == 0)); then
  echo "validate_webhook_examples.sh: no docs/examples/*.sample.json found." >&2
  exit 1
fi
for f in "${samples[@]}"; do
  npx --yes ajv-cli validate -s docs/webhook_payload.schema.json -d "$f"
done
