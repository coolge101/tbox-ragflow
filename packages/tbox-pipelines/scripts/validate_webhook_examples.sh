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

node_major="$(
  node -p "parseInt(process.versions.node.split('.')[0], 10)" 2>/dev/null || echo ""
)"
if [[ -n "$node_major" ]]; then
  # Parity with CI: require at least Node 20, but allow newer majors locally.
  if (( node_major < 20 )); then
    echo "validate_webhook_examples.sh: Node >= 20 is required, got v${node_major}.x (see .node-version)." >&2
    exit 1
  fi
  if (( node_major != 20 )); then
    echo "validate_webhook_examples.sh: warning: CI uses Node 20; you are running Node v${node_major}.x." >&2
  fi
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: npx is required (missing npm/npx). Install npm (Node.js) and retry." >&2
  exit 1
fi

schema="docs/webhook_payload.schema.json"
if [[ ! -f "$schema" ]]; then
  echo "validate_webhook_examples.sh: missing $schema (run from packages/tbox-pipelines)." >&2
  exit 1
fi
shopt -s nullglob
samples=(docs/examples/*.sample.json)
if ((${#samples[@]} == 0)); then
  echo "validate_webhook_examples.sh: no docs/examples/*.sample.json found." >&2
  exit 1
fi
for f in "${samples[@]}"; do
  echo "==> ajv validate: $f"
  npx --yes ajv-cli validate -s "$schema" -d "$f"
done
