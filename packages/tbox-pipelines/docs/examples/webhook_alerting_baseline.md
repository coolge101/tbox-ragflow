# Webhook Alerting Governance Baseline

This baseline provides a production-ready default policy set for webhook alerting.
Use it as the starting point, then tune per environment and business criticality.

## 1) Baseline objectives

- Keep high-signal paging for real delivery failures.
- Detect degradation early through retrying/transport/rate-limit warnings.
- Reduce alert fatigue via grouping, suppression, and phased rollout.
- Keep compatibility stable with `retry_reason_group` + `retry_reason_version`.

## 2) Required signal contract

Minimum parsed fields:

- `event`
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

## 3) Baseline alert classes

### A. Final delivery failure (paging)

- Filter:
  - `event=webhook_notify_failed`
  - `outcome=failure`
  - `delivery_state=failed`
  - `final=True`
- Group by: `payload_type`, `retry_reason_group`, `http_status`, `error_class`

Default thresholds:
- Production critical channel: `>=1 / 5m` (critical page)
- Production non-critical channel: `>=3 / 10m` (high urgency ticket/page)
- Staging/dev: warning only

### B. Retrying spike (warning)

- Filter:
  - `delivery_state=retrying`
  - `final=False`
- Group by: `payload_type`, `retry_reason_group`

Default thresholds:
- Warning when current 15m count > `3x` previous 15m baseline
- Escalate to high urgency when sustained for 30m

### C. Transport instability (warning/high urgency)

- Filter:
  - `retry_reason_group IN (transport_retryable, transport_non_retryable)`
- Group by: `payload_type`, `error_class`

Default thresholds:
- Warning: `>=5 / 10m`
- High urgency: `>=20 / 10m` or multi-channel impact

### D. Rate-limit pressure (warning)

- Filter:
  - `retry_reason_group=http_retryable`
  - `http_status=429`
- Group by: `payload_type`, `sync_id`

Default thresholds:
- Warning: `>=5 / 10m` per `payload_type`
- High urgency: sustained `>=5 / 10m` for 30m on critical integrations

## 4) Environment strategy

### Production

- Enable all four alert classes.
- Paging only for class A and selected sustained class C incidents.
- Require on-call routing and handoff template.

### Staging

- Enable all classes as warning/ticket only.
- Use lower noise tolerance for parser/query validation.
- Run controlled failure drills weekly.

### Dev/Sandbox

- Optional warnings for parser/query debugging.
- No paging.

## 5) Suppression and dedup baseline

- Suppress during approved maintenance windows.
- Deduplicate by:
  - `payload_type`
  - `retry_reason_group`
  - `http_status` (when present)
  - `error_class` (when present)
- Keep minimum cool-down (e.g. 15m) for repeated warning notifications.

## 6) Escalation policy baseline

- Class A production critical: page primary on-call immediately.
- No acknowledgement in 10m: escalate to secondary.
- No mitigation in 30m: involve integration owner + infrastructure owner.
- For class B/C/D sustained >30m on critical flows: raise to incident channel.

## 7) Change management baseline

When updating rules:

1. Propose change with rationale and expected impact.
2. Test in staging for at least one evaluation cycle.
3. Roll out gradually (10%/50%/100% monitor scope if supported).
4. Record threshold/query change in ops changelog.
5. Re-evaluate after 7 days and tune.

## 8) KPI baseline (monthly review)

- Final delivery failure rate by `payload_type`
- Retrying spike frequency
- Transport error share (`transport_*`)
- 429 pressure duration on critical integrations
- Alert noise ratio (non-actionable alerts / total alerts)
- Mean time to acknowledge (MTTA) and resolve (MTTR)

## 9) Compatibility and taxonomy policy

- Route by `retry_reason_group` for long-lived monitor stability.
- Use `retry_reason` for detailed diagnostics only.
- Preserve `retry_reason_version` in parser storage and monitor context.
- If taxonomy evolves, version-gate parsing and keep backward-compatible dashboards during migration.
