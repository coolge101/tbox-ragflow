# Webhook Alert Rules (Loki/Prometheus Sample)

This sample provides Loki LogQL style alert examples for webhook delivery logs.
Adjust label selectors and thresholds for your environment.

Assumptions:
- `webhook_notify_failed` logs are ingested into Loki.
- Pipeline extracts fields such as:
  - `outcome`, `delivery_state`, `final`, `payload_type`
  - `retry_reason_group`, `retry_reason`, `retry_reason_version`
  - `http_status`, `error_class`, `sync_id`

## 1) Final delivery failures (page)

Intent: alert when delivery has already ended in failure.

Example LogQL metric query:

```text
sum by (payload_type, retry_reason_group, http_status, error_class) (
  count_over_time({app="tbox-pipelines"} |= "webhook_notify_failed"
    | logfmt
    | outcome="failure"
    | delivery_state="failed"
    | final="True"
  [5m])
)
```

Suggested rule:
- Critical when any series is `>= 1` for 5m on production-critical channels.

## 2) Retrying spike (warning)

Intent: detect retry bursts before final failures accumulate.

Example LogQL metric query:

```text
sum by (payload_type, retry_reason_group) (
  count_over_time({app="tbox-pipelines"} |= "webhook_notify_failed"
    | logfmt
    | outcome="failure"
    | delivery_state="retrying"
    | final="False"
  [15m])
)
```

Suggested rule:
- Warning when current value is >3x moving baseline (implement with recording rules or dashboard math).

## 3) Transport instability (infra)

Intent: isolate network/TLS/DNS/connectivity issues.

Example LogQL metric query:

```text
sum by (payload_type, error_class) (
  count_over_time({app="tbox-pipelines"} |= "webhook_notify_failed"
    | logfmt
    | retry_reason_group=~"transport_retryable|transport_non_retryable"
  [10m])
)
```

Suggested rule:
- Warning when any series is `>= 5` in 10m.

## 4) Rate-limit pressure (integration)

Intent: identify receiver-side throttling hotspots.

Example LogQL metric query:

```text
sum by (payload_type, sync_id) (
  count_over_time({app="tbox-pipelines"} |= "webhook_notify_failed"
    | logfmt
    | retry_reason_group="http_retryable"
    | http_status="429"
  [10m])
)
```

Suggested rule:
- Warning when count is `>= 5` per `payload_type` in 10m.

## Compatibility recommendations

- Route alert classes by `retry_reason_group` (stable buckets).
- Keep `retry_reason` for drill-down dashboards.
- Persist `retry_reason_version` in parsed labels/fields to support taxonomy evolution.
