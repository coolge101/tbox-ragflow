# Webhook Alerting Render Change Log (Sample)

## Header

- Change ID: RENDER-2026-04-30-001
- Date (UTC): 2026-04-30
- Author: tbox-platform
- Reviewer: code-reviewer
- Related PR: S3.153 rendered monitor bundles
- Effective version: S3.153

## Change scope

- [x] Template + rendered semantic change
- [x] New platform rendered bundle added
- [ ] Existing platform bundle removed/deprecated

## Why this change

- Problem statement: Teams had a generic template but lacked immediately usable platform outputs.
- Expected operational impact: Faster onboarding and less hand-written query drift.
- Risk level: medium

## What changed

### Template changes

- Files:
  - `webhook_alerting_monitor_as_code.template.yaml`
- Fields touched:
  - monitor set confirmation for A/B/C/D classes
  - variable mapping usage clarification
- Invariants affected:
  - none (invariants preserved)

### Rendered bundle changes

- Datadog:
  - Files:
    - `webhook_alerting_monitor_as_code.datadog.rendered.yaml`
  - Query/routing/grouping changes:
    - Added class A/B/C/D log alert examples
    - Preserved grouping keys from template invariants
- Prometheus/Loki:
  - Files:
    - `webhook_alerting_monitor_as_code.prometheus.rendered.yaml`
  - Query/routing/grouping changes:
    - Added class A/B/C/D LogQL expressions
    - Preserved grouping keys from template invariants

## Invariant check summary

- [x] Monitor ID set unchanged
- [x] Grouping keys preserved
- [x] Threshold/window semantics preserved
- [x] Route-by/drill-down policy preserved
- [x] Deviations documented (none)

## Acceptance checklist summary

- [x] Template integrity checks passed
- [x] Rendered parity checks passed
- [x] Query contract checks passed
- [x] Documentation consistency checks passed
- [x] Validation commands passed (`ruff`, `pytest`)

## Rollout and rollback

- Rollout steps:
  1. Publish rendered examples in docs.
  2. Ask platform owners to copy and adapt thresholds.
  3. Validate in staging before prod activation.
- Rollback trigger:
  - Any semantic mismatch discovered between template and rendered examples.
- Rollback steps:
  1. Revert rendered files to previous version.
  2. Re-open drift fix PR with updated change log.

## Post-change verification

- Monitoring window: first 7 days post-adoption
- Signals reviewed: alert volume, false positive ratio, monitor parse errors
- Outcome: stable
- Follow-up actions:
  - Add render spec and merge gate checklist (S3.154)
