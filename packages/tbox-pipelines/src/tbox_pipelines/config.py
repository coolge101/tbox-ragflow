from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    ragflow_base_url: str
    ragflow_api_key: str
    target_dataset_id: str
    target_dataset_name: str
    auto_create_dataset: bool
    auto_run_after_upload: bool


DEFAULT_CONFIG_PATH = Path("config/pipeline.sample.json")


def _to_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def load_config(config_path: str | None = None) -> PipelineConfig:
    env_base_url = os.getenv("RAGFLOW_BASE_URL")
    env_api_key = os.getenv("RAGFLOW_API_KEY", "")
    env_dataset_id = os.getenv("RAGFLOW_DATASET_ID", "")
    env_dataset_name = os.getenv("RAGFLOW_DATASET_NAME", "")
    env_auto_create_dataset = os.getenv("RAGFLOW_AUTO_CREATE_DATASET")
    env_auto_run = os.getenv("RAGFLOW_AUTO_RUN")

    payload: dict[str, str | bool] = {}
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if target_path.exists():
        payload = json.loads(target_path.read_text(encoding="utf-8"))

    base_url = env_base_url or payload.get("ragflow_base_url", "http://localhost:9380")
    api_key = env_api_key or payload.get("ragflow_api_key", "")
    dataset_id = env_dataset_id or payload.get("target_dataset_id", "")
    dataset_name = env_dataset_name or payload.get("target_dataset_name", "")
    auto_create_dataset = _to_bool(
        env_auto_create_dataset,
        _to_bool(payload.get("auto_create_dataset"), True),
    )
    auto_run = _to_bool(env_auto_run, _to_bool(payload.get("auto_run_after_upload"), True))

    return PipelineConfig(
        ragflow_base_url=str(base_url).rstrip("/"),
        ragflow_api_key=str(api_key),
        target_dataset_id=str(dataset_id),
        target_dataset_name=str(dataset_name),
        auto_create_dataset=auto_create_dataset,
        auto_run_after_upload=auto_run,
    )
