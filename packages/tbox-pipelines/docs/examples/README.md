# Webhook Alerting Examples Overview

This directory contains end-to-end artifacts for webhook alert governance,
from platform-neutral contracts to platform-specific rendered monitor samples.

## Document layers

Recommended reading order:

1. Contract and foundation
   - `../WEBHOOK_CONTRACT.md`
   - `webhook_alert_rules.index.md`
2. Rule templates and platform samples
   - `webhook_alert_rules.sample.md`
   - `webhook_alert_rules.datadog.sample.md`
   - `webhook_alert_rules.promql.sample.md`
   - `webhook_alert_rules.openobserve.sample.md`
   - `webhook_alert_rules.elasticsearch.sample.md`
3. Operations and governance
   - `webhook_alert_rules.migration_checklist.md`
   - `webhook_alert_rules.troubleshooting.md`
   - `webhook_alerting_runbook.md`
   - `webhook_alerting_baseline.md`
   - `webhook_alerting_baseline.parameterized.md`
4. Monitor-as-code and render governance
   - `webhook_alerting_monitor_as_code.template.yaml`
   - `webhook_alerting_monitor_as_code.datadog.rendered.yaml`
   - `webhook_alerting_monitor_as_code.prometheus.rendered.yaml`
   - `webhook_alerting_render_spec.md`
   - `webhook_alerting_render_acceptance_checklist.md`
   - `webhook_alerting_render_change_log.template.md`
   - `webhook_alerting_render_change_log.sample.md`

## File roles

- `*.sample.md`:
  - Human-readable rule/query examples by platform.
- `webhook_alerting_baseline*.md`:
  - Policy defaults and parameterized governance baselines.
- `*.template.yaml`:
  - Generic machine-oriented template for downstream rendering.
- `*.rendered.yaml`:
  - Platform-specific examples rendered from generic template semantics.
- `render_spec` / `render_acceptance_checklist`:
  - Guardrails to prevent semantic drift across rendered bundles.
- `render_change_log.*`:
  - Audit trail format for render/template updates.
- `gate_rules_invalid/*.json`:
  - Negative samples for docs gate regression tests.

## Maintenance conventions

1. Semantic changes start from template-level docs:
   - Update baseline/template/spec first.
2. Rendered outputs follow:
   - Keep monitor IDs, grouping keys, and threshold semantics aligned.
3. Update index and references:
   - Ensure `webhook_alert_rules.index.md` and `WEBHOOK_CONTRACT.md` links are complete.
4. Record render changes:
   - Use `webhook_alerting_render_change_log.template.md`.

## Common pitfalls

- Editing rendered files without syncing template/spec.
- Changing query syntax and accidentally changing semantics.
- Missing updates in index/changelog references after adding new files.
- Forgetting to preserve `retry_reason_group` and `retry_reason_version` compatibility policy.

## Minimum merge gate

Before merging docs changes in this directory:

- Run lint/test validation commands used by this project.
- Run `validate-alert-docs-links` from `packages/tbox-pipelines` after `pip install -e .` (or `python -m tbox_pipelines.alert_docs_links_validate_cli` / `python scripts/validate_alert_docs_links.py` with `PYTHONPATH=src`).
  - Use `--verbose` for CI-style diagnostics.
  - Success summary output includes `summary_version` (current `1`) for parser compatibility.
  - Summary metric keys are controlled by `summary_contract.metric_keys` in rules.
  - CI runs the full gate as one command: `alert-docs-gate ci --verbose --log-path ... --emit-json --write-github-output --write-step-summary` (or the separate `validate-alert-docs-links` + `emit-alert-docs-gate-metrics` / `-m` equivalents); the workflow also prints `alert-docs-gate version` inside the same `::group::alert-docs-gate` block before `ci`.
  - Consumer job validates `alert_docs_gate_metrics_json` with `alert-docs-gate metrics-validate` (stdin); standalone `validate-alert-docs-metrics-payload` remains available. CI groups consumer steps under `::group::alert-docs-gate-consumer` and prints `alert-docs-gate version` first. Ignore stray `uv.lock` under `packages/tbox-pipelines` (see `.gitignore` there).
  - Optional: `alert-docs-gate emit --log-path ...` forwards argv to the same emitter as `emit-alert-docs-gate-metrics` (useful outside the built-in `ci` bundle).
  - `alert-docs-gate version` prints the installed `tbox-pipelines` version (PEP 566 metadata).
  - Internal: `_invoke_cli_argv` centralizes argv save/restore for delegated **subcommand** entrypoints.
  - CI metric replay uses `emit-alert-docs-gate-metrics --log-path ...` (or `python -m tbox_pipelines.metrics_emit_cli` / `python scripts/emit_alert_docs_gate_metrics.py` with `PYTHONPATH=src`).
  - Metrics emitter enforces `summary_contract` strictly (event/version/metric_keys).
  - Use `--emit-json` to output `alert_docs_gate_metrics_json` mirror for machine parsing.
  - In GitHub Actions, add `--write-github-output` (with `GITHUB_OUTPUT` set) to publish metrics as step/job outputs (`alert_docs_gate_metrics_kv`, `alert_docs_gate_metrics_json`, etc.).
  - Add `--write-step-summary` (with `GITHUB_STEP_SUMMARY` set) to append a Markdown metrics table to the job step summary.
  - `metrics_emit_contract.emit_version` in rules drives `metrics_emit_version` on emitted metrics payloads.
  - `alert_docs_gate_metrics_payload.schema.json` documents and is enforced for the CI metrics JSON payload shape.
  - `scripts/validate_alert_docs_metrics_payload.py` validates a metrics JSON object against that schema (stdin or `--payload-path`); after `pip install -e .`, use `validate-alert-docs-metrics-payload` or `python -m tbox_pipelines.metrics_payload_validate_cli`. CI consumer job pipes `METRICS_JSON` into the console entry. Implementation lives in `tbox_pipelines.metrics_payload_validate_cli`; shared Draft-07 checks in `tbox_pipelines.alert_docs_gate_metrics_schema`.
  - Metric values must be non-negative integers; invalid types/ranges fail fast.
  - This gate now also checks selected S3 changelog consistency in both
    `README.md` and `WEBHOOK_CONTRACT.md`.
  - Rules are configured in `alert_docs_gate_rules.json` with
    `alert_docs_gate_rules.schema.json` as structure contract.
- Walk through `webhook_alerting_render_acceptance_checklist.md`.
- Confirm cross-file links are still valid.
