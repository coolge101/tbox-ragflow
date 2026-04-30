#!/usr/bin/env python3
"""Validate cross-links for webhook alerting docs examples."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_EXAMPLE_FILES = (
    "README.md",
    "webhook_alert_rules.index.md",
    "webhook_alert_rules.sample.md",
    "webhook_alert_rules.datadog.sample.md",
    "webhook_alert_rules.promql.sample.md",
    "webhook_alert_rules.openobserve.sample.md",
    "webhook_alert_rules.elasticsearch.sample.md",
    "webhook_alert_rules.migration_checklist.md",
    "webhook_alert_rules.troubleshooting.md",
    "webhook_alerting_runbook.md",
    "webhook_alerting_baseline.md",
    "webhook_alerting_baseline.parameterized.md",
    "webhook_alerting_monitor_as_code.template.yaml",
    "webhook_alerting_monitor_as_code.datadog.rendered.yaml",
    "webhook_alerting_monitor_as_code.prometheus.rendered.yaml",
    "webhook_alerting_render_spec.md",
    "webhook_alerting_render_acceptance_checklist.md",
    "webhook_alerting_render_change_log.template.md",
    "webhook_alerting_render_change_log.sample.md",
)


def _missing_links(doc_text: str, expected_tokens: tuple[str, ...]) -> list[str]:
    return [token for token in expected_tokens if token not in doc_text]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    docs = root / "docs"
    examples = docs / "examples"
    index_path = examples / "webhook_alert_rules.index.md"
    contract_path = docs / "WEBHOOK_CONTRACT.md"
    examples_readme_path = examples / "README.md"

    errors: list[str] = []

    for filename in REQUIRED_EXAMPLE_FILES:
        path = examples / filename
        if not path.exists():
            errors.append(f"missing required docs/examples file: {filename}")

    if not index_path.exists():
        errors.append("missing index file: docs/examples/webhook_alert_rules.index.md")
    if not contract_path.exists():
        errors.append("missing contract file: docs/WEBHOOK_CONTRACT.md")
    if not examples_readme_path.exists():
        errors.append("missing examples overview: docs/examples/README.md")

    if errors:
        for err in errors:
            print(f"validate_alert_docs_links.py: error: {err}", file=sys.stderr)
        return 1

    index_text = index_path.read_text(encoding="utf-8")
    contract_text = contract_path.read_text(encoding="utf-8")
    examples_readme_text = examples_readme_path.read_text(encoding="utf-8")

    index_link_expected = tuple(
        name for name in REQUIRED_EXAMPLE_FILES if name != "webhook_alert_rules.index.md"
    )
    index_tokens = tuple(f"[`{name}`]({name})" for name in index_link_expected)
    missing_in_index = _missing_links(index_text, index_tokens)
    for token in missing_in_index:
        errors.append(f"index missing link token: {token}")

    contract_tokens = tuple(
        f"[`examples/{name}`](examples/{name})" for name in REQUIRED_EXAMPLE_FILES
    )
    missing_in_contract = _missing_links(contract_text, contract_tokens)
    for token in missing_in_contract:
        errors.append(f"WEBHOOK_CONTRACT missing link token: {token}")

    readme_must_include = (
        "webhook_alert_rules.index.md",
        "webhook_alerting_monitor_as_code.template.yaml",
        "webhook_alerting_render_spec.md",
    )
    missing_in_examples_readme = _missing_links(examples_readme_text, readme_must_include)
    for token in missing_in_examples_readme:
        errors.append(f"examples README missing token: {token}")

    if errors:
        for err in errors:
            print(f"validate_alert_docs_links.py: error: {err}", file=sys.stderr)
        return 1

    print("validate_alert_docs_links.py: ok all required doc links present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
