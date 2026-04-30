from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "validate_webhook_examples.sh"


def _line_containing(snippet: str) -> str:
    for line in _SCRIPT.read_text(encoding="utf-8").splitlines():
        if snippet in line:
            return line
    msg = f"expected line containing {snippet!r} in {_SCRIPT}"
    raise AssertionError(msg)


def _assert_key_once(line: str, key: str) -> None:
    token = f'\\"{key}\\":'
    assert line.count(token) == 1, f"expected exactly one {key!r} token in line"


def test_start_log_contains_required_canonical_keys() -> None:
    line = _line_containing('start_json="{')
    required_keys = (
        "event",
        "component",
        "log_version",
        "run_id",
        "started_at_utc",
        "cwd",
        "validation_mode",
        "validator_engine",
        "validator_schema_draft",
        "validator_command",
        "run_scope",
        "sample_iteration_mode",
        "sample_validation_unit",
        "sample_elapsed_field",
        "sample_elapsed_unit",
        "sample_index_base",
        "schema",
        "schema_mtime_utc",
        "schema_size_bytes",
        "schema_hash_alg",
        "schema_sha256",
        "samples_dir",
        "samples_glob",
        "sample_count_source",
        "sort_locale",
        "samples",
        "samples_total_bytes",
        "precheck_passed",
    )
    for key in required_keys:
        _assert_key_once(line, key)


def test_start_log_does_not_emit_removed_compat_fields() -> None:
    """Phase C (post 2026-06-30): v1-extended keys must not appear in start_json."""
    line = _line_containing('start_json="{')
    removed_keys = (
        "validator_command_source",
        "validator_invocation",
        "validator_auto_install",
        "sample_result_status_field",
        "sample_total_field",
        "sample_path_field",
        "sample_type_field",
        "samples_glob_applied",
        "samples_sorted",
        "samples_nonempty",
        "sample_count_expected",
        "samples_bytes_computed",
        "schema_exists",
        "schema_hash_verified",
    )
    for key in removed_keys:
        assert f'"{key}"' not in line, f"removed field {key!r} must not appear in start_json"


def test_phase_c_no_tbox_webhook_log_compat_v1() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    assert "LOG_VERSION=2" in text
    assert "TBOX_WEBHOOK_LOG_COMPAT_V1" not in text
    assert "LOG_COMPAT_V1" not in text


def test_start_log_mapping_matches_sample_event_keys() -> None:
    start_line = _line_containing('start_json="{')
    sample_line = _line_containing("sample_validate")

    assert '\\"sample_elapsed_field\\":\\"elapsed_ms\\"' in start_line
    assert '\\"sample_elapsed_unit\\":\\"ms\\"' in start_line
    assert '\\"sample_index_base\\":1' in start_line

    for key in ("status", "elapsed_ms", "index", "total", "path", "sample_type"):
        _assert_key_once(sample_line, key)
