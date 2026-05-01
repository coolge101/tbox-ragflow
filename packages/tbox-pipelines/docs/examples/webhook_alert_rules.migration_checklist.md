# Webhook Alert Rules Migration Checklist

Use this checklist when rolling out webhook alert rules from generic templates
to a concrete log platform.

## 1) Parser readiness

- [ ] Confirm `webhook_notify_failed` lines are ingested.
- [ ] Parse at least these fields:
  - [ ] `event`
  - [ ] `outcome`
  - [ ] `delivery_state`
  - [ ] `final`
  - [ ] `payload_type`
  - [ ] `retry_reason_group`
  - [ ] `retry_reason`
  - [ ] `retry_reason_version`
  - [ ] `http_status`
  - [ ] `error_class`
  - [ ] `sync_id`
- [ ] Verify boolean representation for `final` (`True/False` vs `true/false`) in your platform parser.
- [ ] Verify numeric representation for `http_status` (number vs string) in your platform parser.

## 2) Baseline dashboards

- [ ] Build a top-level panel for `delivery_state=failed` (final failures).
- [ ] Build a top-level panel for `delivery_state=retrying` (in-progress retries).
- [ ] Split both panels by `payload_type`.
- [ ] Add `retry_reason_group` breakdown.
- [ ] Keep a drill-down panel by `retry_reason` for diagnostics.

## 3) Alert rollout (phased)

- [ ] Phase A: enable warning alerts only (`retrying` spike, transport instability).
- [ ] Phase B: enable page-level alerts for `failed final=True`.
- [ ] Phase C: enable 429 pressure alerts (`http_status=429` + `http_retryable`).
- [ ] Add mute windows / maintenance suppression policy.

## 4) Threshold tuning

- [ ] Start with conservative thresholds from sample docs.
- [ ] Observe for one business cycle (at least 7 days recommended).
- [ ] Tune by channel criticality:
  - [ ] critical webhook channel
  - [ ] non-critical webhook channel
- [ ] Document final threshold rationale in your ops runbook.

## 5) Compatibility guardrails

- [ ] Route on `retry_reason_group` (stable).
- [ ] Use `retry_reason` only for drill-down.
- [ ] Keep `retry_reason_version` in parsed model.
- [ ] If taxonomy evolves, version-gate parser logic by `retry_reason_version`.

## 6) Post-rollout validation

- [ ] Trigger a controlled transient failure (e.g., temporary 429 in staging).
- [ ] Verify warning path (`delivery_state=retrying`) is emitted and alerted.
- [ ] Verify final-failure path (`delivery_state=failed final=True`) is emitted and alerted.
- [ ] Verify alert payload includes grouping keys needed for triage.
- [ ] Capture screenshots/links in incident playbook for future onboarding.
