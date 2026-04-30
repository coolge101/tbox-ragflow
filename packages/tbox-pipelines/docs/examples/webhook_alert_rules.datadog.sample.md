# Webhook Alert Rules (Datadog Sample)

This file translates webhook alert templates into Datadog-style query examples.
Adjust service/env tags and thresholds for your deployment.

Assumptions:
- Logs include `event:webhook_notify_failed`.
- Key attributes are parsed as facets/tags:
  - `outcome`, `delivery_state`, `final`, `payload_type`
  - `retry_reason_group`, `retry_reason`, `retry_reason_version`
  - `http_status`, `error_class`, `sync_id`

## 1) Final delivery failures (page)

Intent: page when delivery already ended in failure.

Example log query:

```text
event:webhook_notify_failed outcome:failure delivery_state:failed final:true @payload_type:tbox_sync_summary
```

Example monitor idea:
- Type: log count
- Window: last 5 minutes
- Group by: `@payload_type`, `@retry_reason_group`, `@http_status`, `@error_class`
- Critical: `>= 1` for production-critical channels

## 2) Retrying spike (warning)

Intent: warn on retry bursts before final failures pile up.

Example log query:

```text
event:webhook_notify_failed outcome:failure delivery_state:retrying final:false
```

Example monitor idea:
- Type: logs anomaly or formula monitor
- Group by: `@payload_type`, `@retry_reason_group`
- Condition: current 15m count > 3x previous 15m baseline

## 3) Transport instability (infra)

Intent: isolate network/TLS/DNS/connectivity issues.

Example log query:

```text
event:webhook_notify_failed @retry_reason_group:(transport_retryable OR transport_non_retryable)
```

Example monitor idea:
- Type: log count
- Window: last 10 minutes
- Group by: `@error_class`, `@payload_type`
- Warning: `>= 5`

## 4) Rate-limit pressure (integration)

Intent: identify receiver-side throttling hotspots.

Example log query:

```text
event:webhook_notify_failed @retry_reason_group:http_retryable @http_status:429
```

Example monitor idea:
- Type: log count
- Window: last 10 minutes
- Group by: `@payload_type`, `@sync_id`
- Warning: `>= 5` per `@payload_type`

## Compatibility recommendations

- Route monitors using `@retry_reason_group` (stable bucket).
- Use `@retry_reason` for drill-down dashboards only.
- Keep `@retry_reason_version` in parsed fields to support future taxonomy changes.
