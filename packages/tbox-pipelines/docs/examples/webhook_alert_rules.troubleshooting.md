# Webhook Alert Rules Troubleshooting Guide

This guide helps diagnose noisy, missing, or misrouted webhook alerts.

## Symptom: too many pages

Checks:
- Verify page-level monitor filters include `delivery_state=failed` and `final=True`.
- Verify retrying warnings (`delivery_state=retrying`) are not routed to paging channels.
- Verify grouping keys include `payload_type` and `retry_reason_group` to avoid over-aggregation.

Common fix:
- Split warning and paging routes by `delivery_state`.

## Symptom: no alerts despite known failures

Checks:
- Verify logs contain `event=webhook_notify_failed`.
- Verify parser extracts `delivery_state`, `final`, and `retry_reason_group`.
- Verify boolean conversion for `final` matches platform semantics.
- Verify index/stream/time-range selection includes the target logs.

Common fix:
- Adjust parser field extraction and alert query type casting.

## Symptom: transport and HTTP failures mixed together

Checks:
- Verify routing uses `retry_reason_group`, not only `retry_reason`.
- Verify `retry_reason_group` extraction is exact (no lowercase/uppercase drift).

Common fix:
- Route top-level monitors by `retry_reason_group` and reserve `retry_reason` for drill-down.

## Symptom: high alert churn during incidents

Checks:
- Verify dedup/grouping keys include `payload_type` and optionally `error_class`.
- Verify monitor evaluation windows are not too short (e.g. 1m can be noisy).
- Verify baseline comparison windows are long enough for retry bursts.

Common fix:
- Increase window size and tighten grouping strategy.

## Symptom: 429 alerts not firing

Checks:
- Verify both predicates are present:
  - `retry_reason_group=http_retryable`
  - `http_status=429`
- Verify `http_status` is parsed as expected type (string vs number).

Common fix:
- Normalize status-code field type in parser and align query syntax.

## Quick triage query sequence

1. Base failures: `event=webhook_notify_failed`
2. Final only: `delivery_state=failed final=True`
3. Retrying only: `delivery_state=retrying final=False`
4. Transport bucket: `retry_reason_group in (transport_retryable, transport_non_retryable)`
5. Rate-limit bucket: `retry_reason_group=http_retryable http_status=429`

## Escalation tips

- Include `sync_id`, `payload_type`, `retry_reason_group`, and `error_class` in alert notification payloads.
- When opening incidents, attach one sample raw log and one parsed log record.
- Keep links to dashboard + query in the runbook for faster handoff.
