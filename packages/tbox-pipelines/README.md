# tbox-pipelines

TBOX 文档采集、清洗、调用 RAGFlow HTTP API / SDK 的批处理与工具代码。

## S1 Scaffold（当前）

- CLI：`python -m tbox_pipelines.cli sync`
- 配置：`config/pipeline.sample.json` 或环境变量
  - `RAGFLOW_BASE_URL`
  - `RAGFLOW_API_KEY`
  - `RAGFLOW_DATASET_ID`
  - `RAGFLOW_DATASET_NAME` (when dataset id is empty)
  - `RAGFLOW_AUTO_CREATE_DATASET` (default `true`)
  - `RAGFLOW_AUTO_RUN` (default `true`)
  - `RAGFLOW_HTTP_MAX_RETRIES` (default `2`)
  - `RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS` (default `1.0`)
  - `RAGFLOW_AUDIT_LOG_PATH` (default `logs/sync_audit.jsonl`)
  - `RAGFLOW_RBAC_AUDIT_LOG_PATH` (default `logs/rbac_audit.jsonl`)
  - `RAGFLOW_NOTIFY_WEBHOOK_URL` (optional, fail alerts by default)
  - `RAGFLOW_NOTIFY_ON_SUCCESS` (default `false`)
  - `TBOX_SOURCE_PROVIDER` (`stub` or `http_json`, default `stub`)
  - `TBOX_SOURCE_API_URL` (required when `TBOX_SOURCE_PROVIDER=http_json`)
  - `TBOX_SOURCE_API_KEY` (optional bearer token for source API)
  - `TBOX_SOURCE_TIMEOUT_SECONDS` (default `15.0`)
  - `TBOX_ACTOR_ROLE` (`ingest_bot`/`operator`/`admin`/`viewer`, default `ingest_bot`)
  - `TBOX_RBAC_POLICY_PATH` (optional JSON policy file path, default built-in matrix)
  - `TBOX_RBAC_POLICY_VERSION` (optional policy version string for audit summary)
  - `TBOX_RBAC_POLICY_RELEASE_TAG` (optional release tag for audit summary)
  - `TBOX_RBAC_ALERT_WEBHOOK_URL` (optional webhook for RBAC high-risk failed events)
  - `TBOX_RBAC_ALERT_HIGH_RISK_REASONS` (CSV, default `permission_denied`)
- Airflow 占位 DAG：`airflow/dags/tbox_ingest_dag.py`

> 说明：当前为最小骨架，不接真实 MCP 服务，不写死具体嵌入模型。\n> 入库调用已对齐 RAGFlow `POST /v1/document/upload`（`kb_id` + `file` multipart），
> 并支持在上传后调用 `POST /v1/document/run` 触发解析（默认开启）。
> 网络/服务抖动下会按配置进行重试，并输出结构化 `sync_summary` 日志。
> S2.0 起支持通过 `http_json` 来源读取真实文档（可由 MCP 网关暴露为 HTTP JSON）。
> S2.1 起增加最小 RBAC 矩阵校验（角色-动作授权），未授权会以配置错误退出并记录审计。
> S2.2 起支持从 `rbac_policy_path` 加载角色策略（参考 `config/rbac_policy.sample.json`）。
> S2.3 起在 `sync_summary` 中记录 `rbac_policy_source` 与 `rbac_policy_fingerprint`，用于策略变更审计。
> S2.4 起额外记录 `rbac_policy_version` 与 `rbac_policy_release_tag`，支持发布批次审计。
> S2.5 起将 RBAC 事件单独写入 `rbac_audit_log_path`，与业务同步审计解耦。
> S2.6 起支持 RBAC 高风险失败事件独立告警（默认仅 `permission_denied`）。

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


## CLI 退出码

- `0`：成功
- `2`：配置错误（如 dataset 无法解析）
- `3`：远端/网络错误（RAGFlow API）
- `1`：未知错误

## Airflow dag_run.conf 可选参数

- `dataset_id`
- `dataset_name`
- `auto_create_dataset`
- `auto_run`
- `http_max_retries`
- `http_retry_backoff_seconds`


## 可追溯字段

每次同步会生成 `sync_id`，并：

- 写入上传文档的 Markdown front matter（`source_url`、`sync_id`）
- 透传为 RAGFlow 请求头 `X-Request-Id`
- 出现在 `sync_summary` 结构化日志中


## JSONL 审计日志

每次 `run_sync`（成功或失败）都会向 `audit_log_path` 追加一行 JSON，
字段与 `sync_summary` 一致，可直接用于 Airflow 后续告警或追踪。

- S1.9：Airflow 任务失败时会读取最新失败记录并打印可读摘要
  （格式示例：`sync_failed sync_id=... reason=... uploaded_count=...`）。


## Webhook 告警（轻量）

- 配置 `notify_webhook_url` 后，`run_sync` 会在失败时发送 JSON 告警。
- 若 `notify_on_success=true`，成功也会通知。
- 通知失败不会中断主流程，会记录 `sync_notify` 日志。
