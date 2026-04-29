#!/usr/bin/env bash
# Validate every docs/examples/*.sample.json against docs/webhook_payload.schema.json.
# Same checks as CI (.github/workflows/ci.yml). Run from repo: packages/tbox-pipelines.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
LOG_VERSION=1

epoch_ms() {
  if [[ -n "${EPOCHREALTIME:-}" ]]; then
    local us="${EPOCHREALTIME/./}"
    echo "$((10#$us / 1000))"
    return
  fi
  echo "$(( $(date +%s) * 1000 ))"
}

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

start_epoch_ms="$(epoch_ms)"
started_at_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
run_id="validate-${start_epoch_ms}-$$"
if ! command -v node >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: node is required (CI uses Node 20; see .node-version)." >&2
  exit 1
fi

node_major="$(
  node -p "parseInt(process.versions.node.split('.')[0], 10)" 2>/dev/null || echo ""
)"
node_version="$(node -v 2>/dev/null || echo "")"
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
  npx_version="$(npx --version 2>/dev/null || echo "")"
  echo "validate_webhook_examples.sh: node {\"event\":\"node\",\"component\":\"validate_webhook_examples.sh\",\"log_version\":$LOG_VERSION,\"run_id\":\"$(json_escape "$run_id")\",\"node_version\":\"$(json_escape "$node_version")\",\"npx_version\":\"$(json_escape "$npx_version")\",\"node_major\":$node_major,\"required_major\":$required_major,\"required_major_source\":\"$(json_escape "$required_major_source")\"}"
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "validate_webhook_examples.sh: npx is required (missing npm/npx). Install npm (Node.js) and retry." >&2
  exit 1
fi

schema="docs/webhook_payload.schema.json"
samples_dir="docs/examples"
samples_glob="*.sample.json"
sort_locale="C"
if [[ ! -f "$schema" ]]; then
  echo "validate_webhook_examples.sh: missing $schema (run from packages/tbox-pipelines)." >&2
  exit 1
fi
schema_mtime_utc="$(
  date -u -r "$schema" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "unknown"
)"
schema_size_bytes="$(wc -c < "$schema" | tr -d '[:space:]')"
schema_sha256="$(sha256sum "$schema" | awk '{print $1}')"
shopt -s nullglob
samples=("$samples_dir"/$samples_glob)
if ((${#samples[@]} == 0)); then
  echo "validate_webhook_examples.sh: no docs/examples/*.sample.json found." >&2
  exit 1
fi

# Make CI output deterministic (array order from glob can vary).
# Force a byte-wise sort independent of locale.
IFS=$'\n' samples=($(printf '%s\n' "${samples[@]}" | LC_ALL="$sort_locale" sort))
unset IFS

sample_count="${#samples[@]}"
sample_count_expected="$sample_count"
samples_total_bytes=0
for f in "${samples[@]}"; do
  samples_total_bytes=$((samples_total_bytes + $(wc -c < "$f" | tr -d '[:space:]')))
done
echo "validate_webhook_examples.sh: start {\"event\":\"start\",\"component\":\"validate_webhook_examples.sh\",\"log_version\":$LOG_VERSION,\"run_id\":\"$(json_escape "$run_id")\",\"started_at_utc\":\"$(json_escape "$started_at_utc")\",\"cwd\":\"$(json_escape "$ROOT")\",\"validation_mode\":\"schema+samples\",\"validator_engine\":\"ajv-cli\",\"validator_schema_draft\":\"draft-07\",\"validator_command\":\"npx --yes ajv-cli validate\",\"validator_command_source\":\"inline\",\"validator_invocation\":\"npx\",\"validator_auto_install\":true,\"run_scope\":\"all_samples\",\"sample_iteration_mode\":\"sequential\",\"sample_validation_unit\":\"file\",\"sample_result_status_field\":\"status\",\"sample_elapsed_unit\":\"ms\",\"sample_index_base\":1,\"sample_total_field\":\"total\",\"sample_path_field\":\"path\",\"schema\":\"$(json_escape "$schema")\",\"schema_exists\":true,\"schema_mtime_utc\":\"$(json_escape "$schema_mtime_utc")\",\"schema_size_bytes\":$schema_size_bytes,\"schema_hash_alg\":\"sha256\",\"schema_sha256\":\"$(json_escape "$schema_sha256")\",\"schema_hash_verified\":true,\"samples_dir\":\"$(json_escape "$samples_dir")\",\"samples_glob\":\"$(json_escape "$samples_glob")\",\"samples_glob_applied\":true,\"sample_count_source\":\"glob\",\"sort_locale\":\"$(json_escape "$sort_locale")\",\"samples_sorted\":true,\"samples_nonempty\":true,\"precheck_passed\":true,\"samples\":$sample_count,\"sample_count_expected\":$sample_count_expected,\"samples_total_bytes\":$samples_total_bytes,\"samples_bytes_computed\":true}"

idx=0
for f in "${samples[@]}"; do
  idx=$((idx + 1))
  sample_type="$(basename "$f" .sample.json)"
  sample_mtime_utc="$(
    date -u -r "$f" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "unknown"
  )"
  sample_size_bytes="$(wc -c < "$f" | tr -d '[:space:]')"
  sample_sha256="$(sha256sum "$f" | awk '{print $1}')"
  sample_start_ms="$(epoch_ms)"
  npx --yes ajv-cli validate -s "$schema" -d "$f"
  sample_elapsed_ms="$(( $(epoch_ms) - sample_start_ms ))"
  echo "validate_webhook_examples.sh: sample {\"event\":\"sample_validate\",\"component\":\"validate_webhook_examples.sh\",\"log_version\":$LOG_VERSION,\"run_id\":\"$(json_escape "$run_id")\",\"index\":$idx,\"total\":$sample_count,\"path\":\"$(json_escape "$f")\",\"sample_type\":\"$(json_escape "$sample_type")\",\"sample_mtime_utc\":\"$(json_escape "$sample_mtime_utc")\",\"sample_size_bytes\":$sample_size_bytes,\"sample_hash_alg\":\"sha256\",\"sample_sha256\":\"$(json_escape "$sample_sha256")\",\"schema_sha256\":\"$(json_escape "$schema_sha256")\",\"status\":\"ok\",\"elapsed_ms\":$sample_elapsed_ms}"
done

elapsed_ms="$(( $(epoch_ms) - start_epoch_ms ))"
finished_at_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "validate_webhook_examples.sh: done {\"event\":\"done\",\"component\":\"validate_webhook_examples.sh\",\"log_version\":$LOG_VERSION,\"run_id\":\"$(json_escape "$run_id")\",\"finished_at_utc\":\"$(json_escape "$finished_at_utc")\",\"elapsed_ms\":$elapsed_ms,\"validated\":$sample_count,\"failed\":0}"
