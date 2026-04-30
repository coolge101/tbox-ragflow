# Webhook Alerting Render Specification

This document defines how to render platform-specific monitor bundles from
`webhook_alerting_monitor_as_code.template.yaml`.

## 1) Goal

- Keep semantic parity between generic template and rendered outputs.
- Prevent field drift across Datadog/Prometheus (and future platforms).
- Provide clear rules for manual or scripted rendering workflows.

## 2) Source of truth

- Canonical source: `webhook_alerting_monitor_as_code.template.yaml`
- Rendered targets currently:
  - `webhook_alerting_monitor_as_code.datadog.rendered.yaml`
  - `webhook_alerting_monitor_as_code.prometheus.rendered.yaml`

Rule:
- If semantic conflicts appear, update the template first, then regenerate rendered files.

## 3) Required semantic invariants

The following invariants MUST hold after render:

1. Same monitor set:
   - `final-delivery-failure`
   - `retrying-spike`
   - `transport-instability-warning`
   - `transport-instability-high`
   - `rate-limit-pressure-429`
2. Same routing dimensions:
   - primary route by `retry_reason_group`
   - drill-down via `retry_reason`
3. Same grouping keys per monitor class:
   - A: `payload_type,retry_reason_group,http_status,error_class`
   - B: `payload_type,retry_reason_group`
   - C: `payload_type,error_class`
   - D: `payload_type,sync_id`
4. Same threshold semantics:
   - A final fail threshold/window
   - B retry spike ratio/window
   - C warning/high thresholds/window
   - D 429 threshold/window

## 4) Field mapping rules

## 4.1 Query contract fields

Each rendered monitor must encode these contract predicates:

- Base event: `event=webhook_notify_failed`
- Class A: `outcome=failure`, `delivery_state=failed`, `final=True`
- Class B: `outcome=failure`, `delivery_state=retrying`, `final=False`
- Class C: `retry_reason_group in (transport_retryable, transport_non_retryable)`
- Class D: `retry_reason_group=http_retryable`, `http_status=429`

## 4.2 Type normalization

- Boolean field `final`:
  - Datadog query uses `final:true|false`
  - Loki/logfmt path may require `final="True"|"False"` depending on parser output
- `http_status`:
  - Keep platform-appropriate type (string vs numeric), but preserve equality to `429`

## 5) Rendering workflow

1. Update template variables/structure.
2. Apply platform syntax translation:
   - Datadog logs query DSL
   - Loki LogQL / Prometheus alert expression style
3. Validate monitor IDs and grouping keys unchanged.
4. Validate thresholds/windows aligned with template variables.
5. Update index/changelog references when adding or renaming rendered files.

## 6) Drift policy

- Any rendered-only semantic change is disallowed unless justified and documented.
- Platform syntax-only changes are allowed (no semantic change).
- If a platform cannot represent one invariant exactly, document deviation explicitly in-file.

## 7) Review checklist (quick)

- [ ] Monitor IDs match template
- [ ] Query predicates match class contract
- [ ] Group-by keys preserved
- [ ] Threshold/window semantics preserved
- [ ] Routing and severity intent preserved
- [ ] No undocumented semantic deviations
