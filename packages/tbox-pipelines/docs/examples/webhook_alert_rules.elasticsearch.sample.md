# Webhook Alert Rules (Elasticsearch/KQL Sample)

This sample provides Elasticsearch/Kibana KQL style alert templates for webhook logs.
Adapt index patterns, field names, and thresholds to your environment.

Assumptions:
- `webhook_notify_failed` logs are indexed in Elasticsearch.
- Parsed fields include:
  - `outcome`, `delivery_state`, `final`, `payload_type`
  - `retry_reason_group`, `retry_reason`, `retry_reason_version`
  - `http_status`, `error_class`, `sync_id`

## 1) Final delivery failures (page)

Intent: alert when delivery has already ended in failure.

Example KQL:

```text
event : "webhook_notify_failed" and outcome : "failure" and delivery_state : "failed" and final : true
```

Suggested alert:
- Group by: `payload_type`, `retry_reason_group`, `http_status`, `error_class`
- Critical when count `>= 1` in 5 minutes for production-critical channels.

## 2) Retrying spike (warning)

Intent: detect retry bursts before final failures accumulate.

Example KQL:

```text
event : "webhook_notify_failed" and outcome : "failure" and delivery_state : "retrying" and final : false
```

Suggested alert:
- Group by: `payload_type`, `retry_reason_group`
- Warning when current 15-minute count >3x previous 15-minute baseline.

## 3) Transport instability (infra)

Intent: isolate network/TLS/DNS/connectivity incidents.

Example KQL:

```text
event : "webhook_notify_failed" and retry_reason_group : ("transport_retryable" or "transport_non_retryable")
```

Suggested alert:
- Group by: `payload_type`, `error_class`
- Warning when count `>= 5` in 10 minutes.

## 4) Rate-limit pressure (integration)

Intent: identify receiver-side throttling hotspots.

Example KQL:

```text
event : "webhook_notify_failed" and retry_reason_group : "http_retryable" and http_status : 429
```

Suggested alert:
- Group by: `payload_type`, `sync_id`
- Warning when count `>= 5` in 10 minutes per payload type.

## Compatibility recommendations

- Route monitors using `retry_reason_group` as stable buckets.
- Use `retry_reason` for drill-down and diagnostics only.
- Keep `retry_reason_version` in parsed fields and branch by version when taxonomy evolves.
