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
- Run `python scripts/validate_alert_docs_links.py` from `packages/tbox-pipelines`.
  - Use `python scripts/validate_alert_docs_links.py --verbose` for CI-style diagnostics.
  - Success summary output includes `summary_version` (current `1`) for parser compatibility.
  - Summary metric keys are controlled by `summary_contract.metric_keys` in rules.
  - This gate now also checks selected S3 changelog consistency in both
    `README.md` and `WEBHOOK_CONTRACT.md`.
  - Rules are configured in `alert_docs_gate_rules.json` with
    `alert_docs_gate_rules.schema.json` as structure contract.
- Walk through `webhook_alerting_render_acceptance_checklist.md`.
- Confirm cross-file links are still valid.
