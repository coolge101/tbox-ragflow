#!/usr/bin/env python3
"""Validate cross-links for webhook alerting docs examples."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _validate_rules_payload(payload: object, schema: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["rules schema must be a JSON object"]
    if not isinstance(payload, dict):
        return ["rules payload must be a JSON object"]

    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in payload:
                errors.append(f"rules missing required key: {key}")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return errors

    # required_example_files: array[str]
    ref = payload.get("required_example_files")
    if not isinstance(ref, list) or not ref:
        errors.append("required_example_files must be a non-empty array")
    elif not all(isinstance(item, str) and item for item in ref):
        errors.append("required_example_files must contain non-empty strings")

    # required_changelog_stage_tokens: array[{stage,evidence_tokens}]
    rcs = payload.get("required_changelog_stage_tokens")
    if not isinstance(rcs, list) or not rcs:
        errors.append("required_changelog_stage_tokens must be a non-empty array")
    else:
        for idx, item in enumerate(rcs, start=1):
            if not isinstance(item, dict):
                errors.append(f"required_changelog_stage_tokens[{idx}] must be an object")
                continue
            stage = item.get("stage")
            tokens = item.get("evidence_tokens")
            if not isinstance(stage, str) or not stage.startswith("S") or "." not in stage:
                errors.append(f"required_changelog_stage_tokens[{idx}].stage is invalid")
            if not isinstance(tokens, list) or not tokens:
                errors.append(
                    f"required_changelog_stage_tokens[{idx}]."
                    "evidence_tokens must be non-empty array"
                )
            elif not all(isinstance(tok, str) and tok for tok in tokens):
                errors.append(
                    f"required_changelog_stage_tokens[{idx}].evidence_tokens must contain strings"
                )

    # examples_readme_required_tokens: array[str]
    errt = payload.get("examples_readme_required_tokens")
    if not isinstance(errt, list) or not errt:
        errors.append("examples_readme_required_tokens must be a non-empty array")
    elif not all(isinstance(item, str) and item for item in errt):
        errors.append("examples_readme_required_tokens must contain non-empty strings")

    return errors


def _load_rules(
    root: Path,
) -> tuple[tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...], tuple[str, ...]]:
    rules_path = root / "docs" / "examples" / "alert_docs_gate_rules.json"
    schema_path = root / "docs" / "examples" / "alert_docs_gate_rules.schema.json"
    payload = json.loads(rules_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_errors = _validate_rules_payload(payload, schema)
    if schema_errors:
        msg = "; ".join(schema_errors)
        raise ValueError(f"rules payload failed schema checks: {msg}")

    required_example_files = tuple(payload.get("required_example_files", []))
    stage_rules: list[tuple[str, tuple[str, ...]]] = []
    for item in payload.get("required_changelog_stage_tokens", []):
        stage = str(item.get("stage", "")).strip()
        tokens = tuple(str(t) for t in item.get("evidence_tokens", []))
        if stage:
            stage_rules.append((stage, tokens))
    examples_readme_required_tokens = tuple(payload.get("examples_readme_required_tokens", []))
    return required_example_files, tuple(stage_rules), examples_readme_required_tokens


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
    try:
        (
            required_example_files,
            required_changelog_stage_tokens,
            examples_readme_required_tokens,
        ) = _load_rules(root)
    except Exception as exc:  # noqa: BLE001
        _emit_errors([f"failed to load gate rules json: {exc}"])
        return 1

    for filename in required_example_files:
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
        name for name in required_example_files if name != "webhook_alert_rules.index.md"
    )
    index_tokens = tuple(f"[`{name}`]({name})" for name in index_link_expected)
    missing_in_index = _missing_links(index_text, index_tokens)
    for token in missing_in_index:
        errors.append(f"index missing link token: {token}")

    contract_tokens = tuple(
        f"[`examples/{name}`](examples/{name})" for name in required_example_files
    )
    missing_in_contract = _missing_links(contract_text, contract_tokens)
    for token in missing_in_contract:
        errors.append(f"WEBHOOK_CONTRACT missing link token: {token}")

    missing_in_examples_readme = _missing_links(
        examples_readme_text,
        examples_readme_required_tokens,
    )
    for token in missing_in_examples_readme:
        errors.append(f"examples README missing token: {token}")

    if not readme_root_path.exists():
        errors.append("missing root README.md for changelog checks")
    else:
        readme_root_text = readme_root_path.read_text(encoding="utf-8")
        for stage, tokens in required_changelog_stage_tokens:
            if stage not in readme_root_text:
                errors.append(f"README missing changelog stage token: {stage}")
            for token in tokens:
                if token not in readme_root_text:
                    errors.append(f"README stage {stage} missing evidence token: {token}")

    for stage, tokens in required_changelog_stage_tokens:
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
