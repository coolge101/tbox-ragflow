# Webhook Alerting Governance Baseline (Parameterized Template)

Use this template to roll out alert governance quickly with minimal edits.
Choose a profile (`critical` or `non_critical`), set variables, then apply.

## 1) Profile presets

### Profile: `critical`

- Intended for business-critical webhook channels.
- Recommended defaults:
  - `A_FINAL_FAIL_THRESHOLD=1`
  - `A_FINAL_FAIL_WINDOW=5m`
  - `B_RETRY_SPIKE_MULTIPLIER=3x`
  - `B_RETRY_SPIKE_WINDOW=15m`
  - `C_TRANSPORT_WARN_THRESHOLD=5`
  - `C_TRANSPORT_HIGH_THRESHOLD=20`
  - `C_TRANSPORT_WINDOW=10m`
  - `D_429_WARN_THRESHOLD=5`
  - `D_429_WINDOW=10m`
  - `ESCALATE_NO_ACK=10m`
  - `ESCALATE_NO_MITIGATION=30m`

### Profile: `non_critical`

- Intended for low-risk or internal webhook channels.
- Recommended defaults:
  - `A_FINAL_FAIL_THRESHOLD=3`
  - `A_FINAL_FAIL_WINDOW=10m`
  - `B_RETRY_SPIKE_MULTIPLIER=4x`
  - `B_RETRY_SPIKE_WINDOW=30m`
  - `C_TRANSPORT_WARN_THRESHOLD=10`
  - `C_TRANSPORT_HIGH_THRESHOLD=30`
  - `C_TRANSPORT_WINDOW=15m`
  - `D_429_WARN_THRESHOLD=10`
  - `D_429_WINDOW=15m`
  - `ESCALATE_NO_ACK=20m`
  - `ESCALATE_NO_MITIGATION=60m`

## 2) Required variables

Set these variables in your monitor-as-code or ops runbook:

- `PROFILE` = `critical` or `non_critical`
- `ENV` = `prod` / `staging` / `dev`
- `CHANNEL_NAME` = integration/channel identifier
- `MAINTENANCE_SUPPRESSION` = suppression window policy
- `ONCALL_PRIMARY` = primary owner/team
- `ONCALL_SECONDARY` = escalation owner/team

## 3) Parameterized alert classes

### A. Final delivery failure

- Query contract:
  - `event=webhook_notify_failed`
  - `outcome=failure`
  - `delivery_state=failed`
  - `final=True`
- Grouping:
  - `payload_type`, `retry_reason_group`, `http_status`, `error_class`
- Trigger:
  - `count >= A_FINAL_FAIL_THRESHOLD within A_FINAL_FAIL_WINDOW`

### B. Retrying spike

- Query contract:
  - `delivery_state=retrying`
  - `final=False`
- Grouping:
  - `payload_type`, `retry_reason_group`
- Trigger:
  - `current_window_count >= B_RETRY_SPIKE_MULTIPLIER * previous_window_count`
  - window = `B_RETRY_SPIKE_WINDOW`

### C. Transport instability

- Query contract:
  - `retry_reason_group in (transport_retryable, transport_non_retryable)`
- Grouping:
  - `payload_type`, `error_class`
- Trigger:
  - warning when `count >= C_TRANSPORT_WARN_THRESHOLD` within `C_TRANSPORT_WINDOW`
  - high urgency when `count >= C_TRANSPORT_HIGH_THRESHOLD` within `C_TRANSPORT_WINDOW`

### D. Rate-limit pressure (429)

- Query contract:
  - `retry_reason_group=http_retryable`
  - `http_status=429`
- Grouping:
  - `payload_type`, `sync_id`
- Trigger:
  - warning when `count >= D_429_WARN_THRESHOLD` within `D_429_WINDOW`

## 4) Environment policy matrix

- `prod`
  - enable A/B/C/D
  - paging allowed for A and sustained C
- `staging`
  - enable A/B/C/D as warning/ticket only
- `dev`
  - optional B/C for parser/query validation only

## 5) Suppression and dedup policy

- Apply `MAINTENANCE_SUPPRESSION` during approved windows.
- Dedup key:
  - `payload_type + retry_reason_group + http_status + error_class`
- Recommended warning cool-down:
  - `critical`: 15m
  - `non_critical`: 30m

## 6) Escalation template

- If no acknowledgement within `ESCALATE_NO_ACK` -> page `ONCALL_SECONDARY`.
- If no mitigation within `ESCALATE_NO_MITIGATION` -> involve integration + infrastructure owners.

## 7) Compatibility guardrails

- Route long-lived monitors by `retry_reason_group`.
- Keep `retry_reason` for diagnostics only.
- Keep `retry_reason_version` in parsed output for taxonomy evolution.

## 8) Quick adoption steps

1. Pick `PROFILE`.
2. Fill variables in section 2.
3. Render thresholds/windows into platform queries.
4. Dry-run in staging for one full evaluation cycle.
5. Roll out to prod with phased enablement.
