# Webhook Alert Rules (OpenObserve Sample)

This sample provides OpenObserve-style alert query templates for webhook logs.
Use it as a starting point and adapt stream names, time windows, and thresholds.

Assumptions:
- `webhook_notify_failed` logs are stored in an OpenObserve logs stream.
- Parsed fields include:
  - `outcome`, `delivery_state`, `final`, `payload_type`
  - `retry_reason_group`, `retry_reason`, `retry_reason_version`
  - `http_status`, `error_class`, `sync_id`

## 1) Final delivery failures (page)

Intent: alert when delivery has already ended in hard failure.

Example query idea:

```text
event="webhook_notify_failed" AND outcome="failure" AND delivery_state="failed" AND final=true
```

Suggested alert:
- Group by: `payload_type`, `retry_reason_group`, `http_status`, `error_class`
- Critical when count `>= 1` in 5 minutes for production-critical channels.

## 2) Retrying spike (warning)

Intent: detect retry bursts before final failures accumulate.

Example query idea:

```text
event="webhook_notify_failed" AND outcome="failure" AND delivery_state="retrying" AND final=false
```

Suggested alert:
- Group by: `payload_type`, `retry_reason_group`
- Warning when current 15-minute count is >3x previous 15-minute baseline.

## 3) Transport instability (infra)

Intent: isolate network/TLS/DNS/connectivity incidents.

Example query idea:

```text
event="webhook_notify_failed" AND retry_reason_group IN ("transport_retryable", "transport_non_retryable")
```

Suggested alert:
- Group by: `payload_type`, `error_class`
- Warning when count `>= 5` in 10 minutes.

## 4) Rate-limit pressure (integration)

Intent: identify receiver-side throttling hotspots.

Example query idea:

```text
event="webhook_notify_failed" AND retry_reason_group="http_retryable" AND http_status=429
```

Suggested alert:
- Group by: `payload_type`, `sync_id`
- Warning when count `>= 5` in 10 minutes per payload type.

## Compatibility recommendations

- Prefer `retry_reason_group` for routing and long-lived monitors.
- Use `retry_reason` for drill-down and diagnostics.
- Keep `retry_reason_version` in parsed output and branch by version on future taxonomy changes.
