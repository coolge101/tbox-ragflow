# tbox-pipelines

TBOX 文档采集、清洗、调用 RAGFlow HTTP API / SDK 的批处理与工具代码。

## S1 Scaffold（当前）

- CLI：`python -m tbox_pipelines.cli sync`
- 配置：`config/pipeline.sample.json` 或环境变量
  - `RAGFLOW_BASE_URL`
  - `RAGFLOW_API_KEY`
  - `RAGFLOW_DATASET_ID`
  - `RAGFLOW_AUTO_RUN` (default `true`)
- Airflow 占位 DAG：`airflow/dags/tbox_ingest_dag.py`

> 说明：当前为最小骨架，不接真实 MCP 服务，不写死具体嵌入模型。\n> 入库调用已对齐 RAGFlow `POST /v1/document/upload`（`kb_id` + `file` multipart），
> 并支持在上传后调用 `POST /v1/document/run` 触发解析（默认开启）。

## 本地开发

```bash
cd packages/tbox-pipelines
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tbox_pipelines.cli sync --config config/pipeline.sample.json
# optional: export RAGFLOW_AUTO_RUN=false to upload without triggering parse run
```

## Docker

见本目录 `Dockerfile`，由 `deploy/docker-compose.yml` 中 `tbox-worker` 服务引用（可选启用）。
