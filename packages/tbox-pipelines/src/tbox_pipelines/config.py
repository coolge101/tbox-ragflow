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


DEFAULT_CONFIG_PATH = Path("config/pipeline.sample.json")


def load_config(config_path: str | None = None) -> PipelineConfig:
    env_base_url = os.getenv("RAGFLOW_BASE_URL")
    env_api_key = os.getenv("RAGFLOW_API_KEY", "")
    env_dataset_id = os.getenv("RAGFLOW_DATASET_ID", "")

    payload: dict[str, str] = {}
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if target_path.exists():
        payload = json.loads(target_path.read_text(encoding="utf-8"))

    base_url = env_base_url or payload.get("ragflow_base_url", "http://localhost:9380")
    api_key = env_api_key or payload.get("ragflow_api_key", "")
    dataset_id = env_dataset_id or payload.get("target_dataset_id", "")

    return PipelineConfig(
        ragflow_base_url=base_url.rstrip("/"),
        ragflow_api_key=api_key,
        target_dataset_id=dataset_id,
    )
