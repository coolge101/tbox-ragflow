# Webhook Alerting Render Acceptance Checklist

Use this checklist before merging changes to rendered monitor bundles.

## Scope

Applies to:
- `webhook_alerting_monitor_as_code.template.yaml`
- `webhook_alerting_monitor_as_code.*.rendered.yaml`

## A) Template integrity

- [ ] Template file parses as valid YAML.
- [ ] `version` and `template_id` are present.
- [ ] `variables` block includes A/B/C/D thresholds and windows.
- [ ] `compatibility` block still routes by `retry_reason_group`.
- [ ] `taxonomy_version_field` remains `retry_reason_version`.

## B) Rendered parity checks

- [ ] Rendered bundles include all required monitor IDs:
  - [ ] `final-delivery-failure`
  - [ ] `retrying-spike`
  - [ ] `transport-instability-warning`
  - [ ] `transport-instability-high`
  - [ ] `rate-limit-pressure-429`
- [ ] Each monitor keeps intended severity/routing class.
- [ ] Group-by keys match spec for A/B/C/D classes.
- [ ] All threshold/window values align with rendered profile variables.

## C) Query contract checks

- [ ] Base selector includes `event=webhook_notify_failed`.
- [ ] Class A query enforces final failure semantics.
- [ ] Class B query enforces retrying semantics.
- [ ] Class C query enforces transport bucket semantics.
- [ ] Class D query enforces 429 + `http_retryable`.
- [ ] Boolean and status-code field typing is valid for target platform.

## D) Documentation consistency

- [ ] `webhook_alert_rules.index.md` links all current rendered bundles.
- [ ] `WEBHOOK_CONTRACT.md` sample list includes new/updated files.
- [ ] `README.md` changelog entry reflects this iteration.
- [ ] Any platform-specific semantic deviations are documented.

## E) Validation and merge gate

- [ ] `ruff check` passes.
- [ ] `ruff format --check` passes.
- [ ] `pytest tests -q` passes.
- [ ] PR summary includes what changed in template vs rendered outputs.
- [ ] Reviewer confirms no semantic drift from template invariants.
