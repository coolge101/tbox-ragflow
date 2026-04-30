# Webhook Alerting Runbook

This runbook is a platform-neutral SOP for webhook alert operations.
It complements query samples and focuses on incident handling workflow.

## Scope

- Signal source: `webhook_notify_failed` logs
- Primary routing keys:
  - `delivery_state`
  - `final`
  - `retry_reason_group`
  - `payload_type`

## Severity model

### SEV-1 (page immediately)

Trigger guidance:
- `delivery_state=failed` and `final=True` on production-critical webhook channels
- Repeated failures that block downstream automation or user-facing workflows

Initial objective:
- Stop impact expansion and restore notification delivery quickly.

### SEV-2 (urgent, non-paging or secondary page)

Trigger guidance:
- Sustained `delivery_state=retrying` spikes
- Persistent `transport_*` failures with rising trend
- Repeated `http_status=429` pressure without final failures yet

Initial objective:
- Stabilize before escalation to SEV-1.

### SEV-3 (monitor and optimize)

Trigger guidance:
- Low-volume intermittent retries
- Isolated non-critical channel failures

Initial objective:
- Track trend, tune thresholds, and prevent future noise.

## Triage procedure (first 10 minutes)

1. Confirm event scope:
   - Filter `event=webhook_notify_failed`.
   - Separate `delivery_state=failed` vs `delivery_state=retrying`.
2. Confirm blast radius:
   - Group by `payload_type`.
   - Count affected `sync_id` in current window.
3. Classify failure family:
   - `retry_reason_group=http_retryable/http_non_retryable`
   - `retry_reason_group=transport_retryable/transport_non_retryable`
   - `retry_reason_group=unexpected`
4. Capture minimum evidence:
   - One raw log line
   - One parsed record
   - Current query/dashboard link

## Response playbook by failure group

### HTTP retryable (`http_retryable`)

- Check status distribution (`429`, `5xx`, `408`).
- For `429`: verify receiver throttling policy and consider backoff/retry tuning.
- For `5xx`: contact receiver owner and confirm service health.

### HTTP non-retryable (`http_non_retryable`)

- Inspect status classes (`4xx`) and request validity assumptions.
- Verify endpoint auth/token status and URL correctness.
- Escalate to integration owner with sample request context.

### Transport (`transport_retryable` / `transport_non_retryable`)

- Check DNS/TLS/network path and proxy/firewall changes.
- Inspect `error_class` trend (e.g. timeout/connect errors).
- Coordinate with infrastructure/network team if multi-service impact appears.

### Unexpected (`unexpected`)

- Treat as code-path anomaly until proven otherwise.
- Escalate to pipeline maintainers with stack/error context.
- Consider temporary suppression only after manual confirmation.

## On-call handoff template

Use this structure in shift handoff notes:

- Incident window (UTC):
- Current severity:
- Affected `payload_type`:
- Dominant `retry_reason_group`:
- Top `error_class` / `http_status`:
- Current mitigation:
- Outstanding risks:
- Next check time:
- Dashboard/query links:

## Recovery and closure checklist

- [ ] Alert condition is cleared for at least one full evaluation window.
- [ ] Delivery has resumed on affected channels.
- [ ] Temporary mitigations are documented (or rolled back).
- [ ] Threshold/suppression changes are recorded.
- [ ] Incident note includes sample logs and root-cause hypothesis.

## Post-incident review template

- Summary:
- Customer/business impact:
- Detection timeline:
- Response timeline:
- Root cause:
- Why existing alerts did/did not help:
- Preventive actions:
  - parser/schema improvements
  - threshold tuning
  - route/suppression policy updates
- Owner + due date for each action:

## Compatibility notes

- Keep routing based on `retry_reason_group` for long-term stability.
- Keep `retry_reason` for drill-down only.
- Preserve `retry_reason_version` in parser output for future taxonomy evolution.
