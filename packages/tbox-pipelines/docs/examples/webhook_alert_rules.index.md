# Webhook Alert Rules Index

This index links all webhook alert rule samples and provides a quick field-mapping
reference across different log/monitoring platforms.

## Sample files

- Generic template: [`webhook_alert_rules.sample.md`](webhook_alert_rules.sample.md)
- Datadog style: [`webhook_alert_rules.datadog.sample.md`](webhook_alert_rules.datadog.sample.md)
- Loki/Prometheus style: [`webhook_alert_rules.promql.sample.md`](webhook_alert_rules.promql.sample.md)
- OpenObserve style: [`webhook_alert_rules.openobserve.sample.md`](webhook_alert_rules.openobserve.sample.md)
- Elasticsearch/KQL style: [`webhook_alert_rules.elasticsearch.sample.md`](webhook_alert_rules.elasticsearch.sample.md)

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
