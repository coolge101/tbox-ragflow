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

REQUIRED_CHANGELOG_STAGE_TOKENS = (
    (
        "S3.153",
        "webhook_alerting_monitor_as_code.datadog.rendered.yaml",
        "webhook_alerting_monitor_as_code.prometheus.rendered.yaml",
    ),
    (
        "S3.154",
        "webhook_alerting_render_spec.md",
        "webhook_alerting_render_acceptance_checklist.md",
    ),
    (
        "S3.155",
        "webhook_alerting_render_change_log.template.md",
        "webhook_alerting_render_change_log.sample.md",
    ),
    ("S3.156", "docs/examples/README.md"),
    ("S3.157", "validate_alert_docs_links.py"),
    ("S3.158", "validate_alert_docs_links.py", "CI"),
)


def _missing_links(doc_text: str, expected_tokens: tuple[str, ...]) -> list[str]:
    return [token for token in expected_tokens if token not in doc_text]


def _emit_errors(errors: list[str]) -> None:
    print(
        f"validate_alert_docs_links.py: fail total_errors={len(errors)}",
        file=sys.stderr,
    )
    for idx, err in enumerate(errors, start=1):
        print(f"validate_alert_docs_links.py: error[{idx}] {err}", file=sys.stderr)


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
        _emit_errors(errors)
        return 1

    index_text = index_path.read_text(encoding="utf-8")
    contract_text = contract_path.read_text(encoding="utf-8")
    examples_readme_text = examples_readme_path.read_text(encoding="utf-8")
    readme_root_path = root / "README.md"

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

    if not readme_root_path.exists():
        errors.append("missing root README.md for changelog checks")
    else:
        readme_root_text = readme_root_path.read_text(encoding="utf-8")
        for stage, *tokens in REQUIRED_CHANGELOG_STAGE_TOKENS:
            if stage not in readme_root_text:
                errors.append(f"README missing changelog stage token: {stage}")
            for token in tokens:
                if token not in readme_root_text:
                    errors.append(f"README stage {stage} missing evidence token: {token}")

    for stage, *tokens in REQUIRED_CHANGELOG_STAGE_TOKENS:
        if stage not in contract_text:
            errors.append(f"WEBHOOK_CONTRACT missing changelog stage token: {stage}")
        for token in tokens:
            if token not in contract_text:
                errors.append(f"WEBHOOK_CONTRACT stage {stage} missing evidence token: {token}")

    if errors:
        _emit_errors(errors)
        return 1

    print("validate_alert_docs_links.py: ok all required doc links present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
