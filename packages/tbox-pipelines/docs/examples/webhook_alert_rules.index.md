# Webhook Alert Rules Index

This index links all webhook alert rule samples and provides a quick field-mapping
reference across different log/monitoring platforms.

## Sample files

- Directory overview: [`README.md`](README.md)
- Generic template: [`webhook_alert_rules.sample.md`](webhook_alert_rules.sample.md)
- Datadog style: [`webhook_alert_rules.datadog.sample.md`](webhook_alert_rules.datadog.sample.md)
- Loki/Prometheus style: [`webhook_alert_rules.promql.sample.md`](webhook_alert_rules.promql.sample.md)
- OpenObserve style: [`webhook_alert_rules.openobserve.sample.md`](webhook_alert_rules.openobserve.sample.md)
- Elasticsearch/KQL style: [`webhook_alert_rules.elasticsearch.sample.md`](webhook_alert_rules.elasticsearch.sample.md)
- Migration checklist: [`webhook_alert_rules.migration_checklist.md`](webhook_alert_rules.migration_checklist.md)
- Troubleshooting guide: [`webhook_alert_rules.troubleshooting.md`](webhook_alert_rules.troubleshooting.md)
- Operations runbook: [`webhook_alerting_runbook.md`](webhook_alerting_runbook.md)
- Governance baseline pack: [`webhook_alerting_baseline.md`](webhook_alerting_baseline.md)
- Parameterized baseline template: [`webhook_alerting_baseline.parameterized.md`](webhook_alerting_baseline.parameterized.md)
- Monitor-as-code template: [`webhook_alerting_monitor_as_code.template.yaml`](webhook_alerting_monitor_as_code.template.yaml)
- Datadog rendered monitor bundle: [`webhook_alerting_monitor_as_code.datadog.rendered.yaml`](webhook_alerting_monitor_as_code.datadog.rendered.yaml)
- Prometheus rendered monitor bundle: [`webhook_alerting_monitor_as_code.prometheus.rendered.yaml`](webhook_alerting_monitor_as_code.prometheus.rendered.yaml)
- Render specification: [`webhook_alerting_render_spec.md`](webhook_alerting_render_spec.md)
- Render acceptance checklist: [`webhook_alerting_render_acceptance_checklist.md`](webhook_alerting_render_acceptance_checklist.md)
- Render change log template: [`webhook_alerting_render_change_log.template.md`](webhook_alerting_render_change_log.template.md)
- Render change log sample: [`webhook_alerting_render_change_log.sample.md`](webhook_alerting_render_change_log.sample.md)

## Core rule categories

All sample files cover the same four categories:

1. Final delivery failures (`delivery_state=failed`, `final=True`)
2. Retrying spike (`delivery_state=retrying`, `final=False`)
3. Transport instability (`retry_reason_group=transport_*`)
4. Rate-limit pressure (`retry_reason_group=http_retryable`, `http_status=429`)

## Field mapping quick reference

Use these logical fields as the stable contract, then adapt to each platform's query syntax.

| Logical field | Typical value example | Notes |
|---|---|---|
| `event` | `webhook_notify_failed` | Base event selector for failure alerts |
| `outcome` | `failure` | Keeps filters aligned with success/failure semantics |
| `delivery_state` | `retrying` / `failed` | Primary routing for warning vs final-page alerts |
| `final` | `True` / `False` | Explicit finality marker on failure path |
| `payload_type` | `tbox_sync_summary` | Useful service/flow split key |
| `retry_reason_group` | `http_retryable` | Stable bucket for long-lived monitor routes |
| `retry_reason` | `http_429` | Drill-down detail; may evolve with taxonomy |
| `retry_reason_version` | `1` | Compatibility anchor for taxonomy evolution |
| `http_status` | `429` | HTTP-side diagnostics |
| `error_class` | `HTTPStatusError` | Transport/http exception grouping |
| `sync_id` | `sync-2026-...` | Correlation for per-run troubleshooting |

## Compatibility recommendations

- Build long-lived routing on `retry_reason_group`.
- Keep parser output for both `retry_reason` and `retry_reason_version`.
- Use `retry_reason` for detailed drill-down, not top-level paging splits.

## Suggested adoption path

1. Start from [`webhook_alert_rules.sample.md`](webhook_alert_rules.sample.md)
2. Choose platform-specific syntax sample
3. Execute [`webhook_alert_rules.migration_checklist.md`](webhook_alert_rules.migration_checklist.md)
4. During pilot, use [`webhook_alert_rules.troubleshooting.md`](webhook_alert_rules.troubleshooting.md)
5. Run production operations with [`webhook_alerting_runbook.md`](webhook_alerting_runbook.md)
6. Standardize long-term policy with [`webhook_alerting_baseline.md`](webhook_alerting_baseline.md)
7. Operationalize quickly using [`webhook_alerting_baseline.parameterized.md`](webhook_alerting_baseline.parameterized.md)
8. Render platform rules from [`webhook_alerting_monitor_as_code.template.yaml`](webhook_alerting_monitor_as_code.template.yaml)
9. Start from rendered examples for Datadog/Prometheus and tune thresholds per channel
10. Apply [`webhook_alerting_render_spec.md`](webhook_alerting_render_spec.md) and
    [`webhook_alerting_render_acceptance_checklist.md`](webhook_alerting_render_acceptance_checklist.md)
    before merge
11. Record each render update using
    [`webhook_alerting_render_change_log.template.md`](webhook_alerting_render_change_log.template.md)
12. Run `python scripts/validate_alert_docs_links.py` to verify key cross-links
