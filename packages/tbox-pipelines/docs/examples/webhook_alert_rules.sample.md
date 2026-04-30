# Webhook Alert Rules (Sample)

This sample shows practical alert routing rules based on `webhook_notify_failed` logs.
Use it as a copy-and-adapt template for your log platform (Datadog, Grafana, ELK, etc.).

## Required log fields

- `outcome`
- `delivery_state`
- `final`
- `payload_type`
- `retry_reason_group`
- `retry_reason`
- `retry_reason_version`
- `http_status`
- `error_class`
- `sync_id`

## Rule 1: Final delivery failure (page)

- Intent: catch webhook deliveries that ended in a hard failure.
- Filter:
  - `event=webhook_notify_failed`
  - `outcome=failure`
  - `delivery_state=failed`
  - `final=True`
- Group by: `payload_type`, `retry_reason_group`, `http_status`, `error_class`
- Suggested trigger:
  - `count >= 1` in 5 minutes for production critical channels, OR
  - `count >= 3` in 10 minutes for non-critical channels.

## Rule 2: Retrying spike (warning)

- Intent: detect upstream instability before final failures accumulate.
- Filter:
  - `event=webhook_notify_failed`
  - `outcome=failure`
  - `delivery_state=retrying`
  - `final=False`
- Group by: `payload_type`, `retry_reason_group`
- Suggested trigger:
  - current 15-minute count > 3x previous 15-minute baseline.

## Rule 3: Transport instability (infra)

- Intent: quickly isolate network/TLS/DNS/connectivity issues.
- Filter:
  - `event=webhook_notify_failed`
  - `retry_reason_group IN (transport_retryable, transport_non_retryable)`
- Group by: `error_class`, `payload_type`
- Suggested trigger:
  - `count >= 5` in 10 minutes.

## Rule 4: Rate-limit pressure (integration)

- Intent: detect receiver-side throttling hotspots.
- Filter:
  - `event=webhook_notify_failed`
  - `retry_reason_group=http_retryable`
  - `http_status=429`
- Group by: `payload_type`, `sync_id`
- Suggested trigger:
  - `count >= 5` in 10 minutes per `payload_type`, OR
  - `count >= 3` in 5 minutes for one `sync_id`.

## Parser compatibility guidance

- Prefer `retry_reason_group` for long-lived dashboards and routing.
- Use `retry_reason` for detailed drill-down only.
- Keep `retry_reason_version` in your parser output model.
- When taxonomy changes in future versions, branch parser logic by `retry_reason_version`.
