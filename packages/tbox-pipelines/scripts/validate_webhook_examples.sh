#!/usr/bin/env bash
# Validate every docs/examples/*.sample.json against docs/webhook_payload.schema.json.
# Same checks as CI (.github/workflows/ci.yml). Run from repo: packages/tbox-pipelines.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

epoch_ms() {
  if [[ -n "${EPOCHREALTIME:-}" ]]; then
    local us="${EPOCHREALTIME/./}"
    echo "$((10#$us / 1000))"
    return
  fi
  echo "$(( $(date +%s) * 1000 ))"
}

start_epoch_ms="$(epoch_ms)"
started_at_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if ! command -v node >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: node is required (CI uses Node 20; see .node-version)." >&2
  exit 1
fi

node_major="$(
  node -p "parseInt(process.versions.node.split('.')[0], 10)" 2>/dev/null || echo ""
)"
if [[ -n "$node_major" ]]; then
  node_version_file="$ROOT/.node-version"
  required_major=""
  required_major_source="file"
  if [[ -f "$node_version_file" ]]; then
    required_major="$(cat "$node_version_file" | awk -F. '{print $1}' | tr -cd '0-9' || echo "")"
  fi
  if [[ -z "$required_major" ]]; then
    required_major="20"
    required_major_source="default"
    echo "validate_webhook_examples.sh: warning: invalid or missing .node-version; defaulting required Node major to 20." >&2
  fi

  # Parity with CI: require Node >= required_major, but allow newer majors locally.
  if (( node_major < required_major )); then
    echo "validate_webhook_examples.sh: Node >= $required_major is required, got v${node_major}.x (see .node-version)." >&2
    exit 1
  fi
  if (( node_major != required_major )); then
    echo "validate_webhook_examples.sh: warning: CI uses Node major v$required_major; you are running Node v${node_major}.x." >&2
  fi
  echo "validate_webhook_examples.sh: node_major=$node_major required_major=$required_major required_major_source=$required_major_source"
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

# Make CI output deterministic (array order from glob can vary).
# Force a byte-wise sort independent of locale.
IFS=$'\n' samples=($(printf '%s\n' "${samples[@]}" | LC_ALL=C sort))
unset IFS

sample_count="${#samples[@]}"
echo "validate_webhook_examples.sh: started_at_utc=$started_at_utc cwd=$ROOT schema=$schema samples=$sample_count"

idx=0
for f in "${samples[@]}"; do
  idx=$((idx + 1))
  echo "==> ajv validate [$idx/$sample_count]: $f"
  npx --yes ajv-cli validate -s "$schema" -d "$f"
done

elapsed_ms="$(( $(epoch_ms) - start_epoch_ms ))"
finished_at_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "validate_webhook_examples.sh: done validated=$sample_count failed=0 elapsed_ms=$elapsed_ms finished_at_utc=$finished_at_utc"
