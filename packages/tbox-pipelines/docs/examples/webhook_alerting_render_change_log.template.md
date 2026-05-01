# Webhook Alerting Render Change Log Template

Use this template to record any change related to:
- `webhook_alerting_monitor_as_code.template.yaml`
- `webhook_alerting_monitor_as_code.*.rendered.yaml`

## Header

- Change ID:
- Date (UTC):
- Author:
- Reviewer:
- Related PR:
- Effective version:

## Change scope

- [ ] Template-only change
- [ ] Rendered-only syntax change (no semantic change)
- [ ] Template + rendered semantic change
- [ ] New platform rendered bundle added
- [ ] Existing platform bundle removed/deprecated

## Why this change

- Problem statement:
- Expected operational impact:
- Risk level: low / medium / high

## What changed

### Template changes

- Files:
- Fields touched:
- Invariants affected (if any):

### Rendered bundle changes

- Datadog:
  - Files:
  - Query/routing/grouping changes:
- Prometheus/Loki:
  - Files:
  - Query/routing/grouping changes:
- Other platforms:
  - Files:
  - Query/routing/grouping changes:

## Invariant check summary

Reference: `webhook_alerting_render_spec.md`

- [ ] Monitor ID set unchanged (or explicitly documented)
- [ ] Grouping keys preserved
- [ ] Threshold/window semantics preserved
- [ ] Route-by/drill-down policy preserved
- [ ] Deviations documented

## Acceptance checklist summary

Reference: `webhook_alerting_render_acceptance_checklist.md`

- [ ] Template integrity checks passed
- [ ] Rendered parity checks passed
- [ ] Query contract checks passed
- [ ] Documentation consistency checks passed
- [ ] Validation commands passed (`ruff`, `pytest`)

## Rollout and rollback

- Rollout steps:
- Rollback trigger:
- Rollback steps:

## Post-change verification

- Monitoring window:
- Signals reviewed:
- Outcome:
- Follow-up actions (if any):
