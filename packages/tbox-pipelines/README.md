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
  - `TBOX_RBAC_ALERT_DEDUPE_WINDOW_SECONDS` (default `300`, set `0` to disable dedupe)
  - `TBOX_RBAC_ALERT_DEDUPE_STATE_PATH` (default `logs/rbac_alert_dedupe.json`)
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
> S2.7 起对 RBAC 告警做时间窗去重（`reason+fingerprint+role`）。
> S2.8 起在去重窗口内累计抑制次数，下次允许发送时在 webhook 负载中带 `rbac_alert_suppressed_in_window` 汇总。
> S2.9 起 RBAC 告警 webhook 使用独立负载类型 `tbox_rbac_alert`（`rbac` 字段承载完整事件），与 `tbox_sync_summary` 区分。
> S3.0 起约定 webhook 信封字段 `payload_version`，并文档化负载契约（见 `docs/WEBHOOK_CONTRACT.md`）。
> S3.1 起提供 Draft-07 JSON Schema（`docs/webhook_payload.schema.json`）及文档内 `curl` 示例负载。
> S3.2 起在 `docs/examples/` 提供可校验、可复制的示例 JSON 文件。
> S3.3 起 CI（`.github/workflows/ci.yml`）用 `ajv-cli` 校验示例与 `docs/webhook_payload.schema.json` 一致。
> S3.4 起在 `docs/WEBHOOK_CONTRACT.md` 写明 CI 与上文 `ajv-cli` 命令一致，便于对照排错。
> S3.5 起提供 `scripts/validate_webhook_examples.sh`，本地与 CI 共用同一校验入口。
> S3.6 起脚本在无 `node` 时失败并提示；根目录提供 `.node-version`（20）与 CI 对齐。
> S3.7 起 `validate_webhook_examples.sh` 遍历 `docs/examples/*.sample.json`，新增示例无需改脚本。
> S3.8 起脚本检查 schema 文件存在，并在校验每个示例时打印 `==> ajv validate: …` 便于读 CI 日志。
> S3.9 起 `pytest` 对 `docs/examples/*.sample.json` 做信封与 JSON 可解析性检查（无 Node），与 ajv 互补。
> S3.10 起 CI 先跑 `pytest` 再装 Node / 跑 `validate_webhook_examples.sh`，失败更快、少拉 npx。
> S3.11 起 `pytest` 额外校验 `docs/webhook_payload.schema.json` 可解析且含 Draft-07 `oneOf` / `definitions`。
> S3.12 起 `pytest` 进一步断言 schema 的 `oneOf` 为两条 `$ref`、`definitions` 含 `envelope` 与两种 payload 定义。
> S3.13 起 `pytest` 断言示例中信封 `sync_id` 与内层 `summary` / `rbac` 的 `sync_id` 一致（与 `notify.py` 行为对齐）。
> S3.14 起 `pytest` 断言信封 `status` 与内层 `summary.status` / `rbac.status` 一致（缺省按 `unknown`，与 `notify.py` 一致）。
> S3.15 起 `pytest` 断言示例文件名 `<type>.sample.json` 与信封 `type` 一致，避免示例与文件名错配。
> S3.16 起 `pytest` 断言 `docs/examples/*.sample.json` 的文件名集合与 schema 中全部 payload `type` 一致（各一条示例）。
> S3.17 起从 `webhook_payload.schema.json` 的 `oneOf` 解析 payload `type` 集合，避免与 schema 手工双写常量。
> S3.18 起从各 payload 定义的 `allOf[].required` 解析内层对象键（如 `summary`/`rbac`），信封断言不再硬编码分支。
> S3.19 起 `pytest` 断言各 payload definition 中 `properties.type.const` 与 definition 名（及信封 `type`）一致。
> S3.20 起 `pytest` 断言示例内层 `summary`/`rbac` 含字符串 `status`，与审计负载形态一致。
> S3.21 起 `pytest` 断言内层同样显式含字符串 `sync_id`（与信封一致）。
> S3.22 起 `pytest` 断言示例含完整顶层信封键及内层键，且信封/内层 `sync_id` 非空字符串。
> S3.23 起 `pytest` 额外断言信封/内层 `status` 为非空字符串。
> S3.24 起 `pytest` 断言示例只包含当前 payload 对应的内层键（不混入其他类型的 body 键）。
> S3.25 起 `pytest` 断言示例顶层键集合精确为信封键 + 当前 payload 的内层键（不多不少）。
> S3.26 起 `pytest` 断言内层对象非空且键名为非空白字符串，减少脏样本。
> S3.27 起 `pytest` 断言示例中 `type`/`status`/`sync_id` 无首尾空白。
> S3.28 起 `pytest` 对示例改为校验信封 `status` 与内层 `status` 直接相等。
> S3.29 起 `pytest` 断言示例中的 `payload_version` 为严格整数（不允许 bool）。
> S3.30 起 `scripts/validate_webhook_examples.sh` 从 `packages/tbox-pipelines/.node-version` 读取目标 Node 主版本，并要求本地 Node >= 该主版本（CI uses Node 20）。
> S3.31 起 `validate_webhook_examples.sh` 检查本地 `npx` 是否可用（缺失则提示安装 npm/Node）。
> S3.32 起 CI 的 `actions/setup-node` 使用 `packages/tbox-pipelines/.node-version` 读取 Node 版本，避免版本漂移。
> S3.33 起脚本在缺失/解析失败时默认 required Node major=20，并给出明确提示。
> S3.34 起脚本对示例文件排序，确保执行顺序确定。
> S3.35 起 CI 额外跑 `bash -n` 校验 validate 脚本语法。
> S3.36 起 CI 将 `bash -n` 提前到 `setup-node` 之前执行。
> S3.37 起 CI 额外校验 `.node-version` 为纯数字 Node major。
> S3.38 起脚本对示例文件排序使用 `LC_ALL=C sort`，避免不同 locale 下排序漂移。
> S3.39 起脚本执行前打印 schema 路径与样本数量，便于 CI 日志排障。
> S3.40 起脚本结束时打印 `done validated=<N>` 收尾日志。
> S3.41 起脚本收尾日志增加 `elapsed_ms`，便于观察校验阶段耗时。
> S3.42 起 `elapsed_ms` 采用毫秒级时间源（`EPOCHREALTIME` 优先），短任务耗时更准确。
> S3.43 起脚本会输出 `node_major` 与 `required_major`，便于 CI 排障。
> S3.44 起脚本在每个样本校验日志中输出进度 `[i/N]`。
> S3.45 起脚本起始日志增加 `started_at_utc`。
> S3.46 起脚本收尾日志增加 `finished_at_utc`。
> S3.47 起脚本会输出 `required_major_source`（`file`/`default`）。
> S3.48 起脚本起始日志增加 `cwd`。
> S3.49 起脚本收尾日志显式输出 `failed=0`（成功路径）。
> S3.50 起脚本收尾日志字段顺序固定为 `finished_at_utc elapsed_ms validated failed`，便于稳定解析。
> S3.51 起脚本收尾日志改为单行 JSON（保留 `finished_at_utc`/`elapsed_ms`/`validated`/`failed` 字段）。
> S3.52 起脚本起始日志也改为单行 JSON（`started_at_utc`/`cwd`/`schema`/`samples`）。
> S3.53 起 Node 版本上下文日志也改为单行 JSON（`node_major`/`required_major`/`required_major_source`）。
> S3.54 起 start/node/done 三类 JSON 日志统一增加 `event` 字段。
> S3.55 起 start/node/done 三类 JSON 日志统一增加 `component` 字段。
> S3.56 起 start/node/done 三类 JSON 日志统一增加 `run_id`，用于单次执行内关联。
> S3.57 起 `node` 日志增加 `node_version` 与 `npx_version` 字段。
> S3.58 起每个样本校验日志改为单行 JSON（`sample_validate`，含 index/total/path）。
> S3.59 起 `sample_validate` 日志增加 `status` 与单样本 `elapsed_ms`。
> S3.60 起起始日志增加 `schema_mtime_utc`，便于确认当次 schema 版本。
> S3.61 起 start/node/sample/done JSON 日志统一增加 `log_version`（当前为 `1`）。
> S3.62 起 `sample_validate` 日志增加 `sample_type`（由 `<type>.sample.json` 推导）。
> S3.63 起 `sample_validate` 日志增加 `sample_size_bytes`。
> S3.64 起 `sample_validate` 日志增加 `sample_sha256`。
> S3.65 起 `sample_validate` 日志增加 `sample_hash_alg`（当前 `sha256`）。
> S3.66 起 `start` 日志增加 `schema_sha256`，用于 schema 内容指纹追踪。
> S3.67 起 `start` 日志增加 `schema_size_bytes`。
> S3.68 起 `start` 日志增加 `samples_total_bytes`。
> S3.69 起 `sample_validate` 日志增加 `schema_sha256`，便于单行关联 schema 指纹。
> S3.70 起 `sample_validate` 日志增加 `sample_mtime_utc`。
> S3.71 起 `start` 日志增加 `schema_hash_alg`（当前 `sha256`）。
> S3.72 起 `start` 日志增加 `samples_dir`（当前 `docs/examples`）。
> S3.73 起 `start` 日志增加 `samples_glob`（当前 `*.sample.json`）。
> S3.74 起 `start` 日志增加 `sort_locale`（当前 `C`）。
> S3.75 起 `start` 日志增加 `sample_count_expected` 字段。
> S3.76 起 `start` 日志增加 `samples_sorted=true` 字段，明确样本已完成确定性排序。
> S3.77 起 `start` 日志增加 `schema_exists=true` 字段，显式标识 schema 已通过存在性检查。
> S3.78 起 `start` 日志增加 `samples_nonempty=true` 字段，显式标识样本存在性检查已通过。
> S3.79 起 `start` 日志增加 `precheck_passed=true` 字段，聚合标识前置检查已通过。
> S3.80 起 `start` 日志增加 `validation_mode="schema+samples"` 字段，显式标识当前校验模式。
> S3.81 起 `start` 日志增加 `sample_count_source="glob"` 字段，显式标识样本计数来源。
> S3.82 起 `start` 日志增加 `run_scope="all_samples"` 字段，显式标识本次运行覆盖范围。
> S3.83 起 `start` 日志增加 `validator_engine="ajv-cli"` 字段，显式标识 schema 校验引擎。
> S3.84 起 `start` 日志增加 `validator_command="npx --yes ajv-cli validate"` 字段，显式标识校验命令。
> S3.85 起 `start` 日志增加 `validator_command_source="inline"` 字段，显式标识校验命令来源。
> S3.86 起 `start` 日志增加 `validator_invocation="npx"` 字段，显式标识校验调用方式。
> S3.87 起 `start` 日志增加 `validator_auto_install=true` 字段，显式标识 `npx --yes` 自动安装语义。
> S3.88 起 `start` 日志增加 `validator_schema_draft="draft-07"` 字段，显式标识当前 schema 草案版本。
> S3.89 起 `start` 日志增加 `schema_hash_verified=true` 字段，显式标识 schema 哈希已计算并写入日志。
> S3.90 起 `start` 日志增加 `samples_bytes_computed=true` 字段，显式标识样本总字节数已完成计算。
> S3.91 起 `start` 日志增加 `samples_glob_applied=true` 字段，显式标识样本 glob 已应用于本次扫描。
> S3.92 起 `start` 日志增加 `sample_iteration_mode="sequential"` 字段，显式标识样本按顺序逐个校验。
> S3.93 起 `start` 日志增加 `sample_validation_unit="file"` 字段，显式标识校验粒度为逐文件。
> S3.94 起 `start` 日志增加 `sample_result_status_field="status"` 字段，显式标识 sample 结果状态字段名。
> S3.95 起 `start` 日志增加 `sample_elapsed_unit="ms"` 字段，显式标识 sample 级耗时字段单位。
> S3.96 起 `start` 日志增加 `sample_index_base=1` 字段，显式标识 sample 索引从 1 开始。
> S3.97 起 `start` 日志增加 `sample_total_field="total"` 字段，显式标识 sample 总量字段名。
> S3.98 起 `start` 日志增加 `sample_path_field="path"` 字段，显式标识 sample 路径字段名。
> S3.99 起 `start` 日志增加 `sample_type_field="sample_type"` 字段，显式标识 sample 类型字段名。
> S3.100 起 `start` 日志增加 `sample_elapsed_field="elapsed_ms"` 字段，显式标识 sample 耗时字段名。
> S3.101 起进入 Phase B：`start` 日志默认输出 canonical 字段集并升级 `log_version=2`；曾支持 `TBOX_WEBHOOK_LOG_COMPAT_V1=true` 追加 deprecated 字段（**S3.103 已移除**）。
> S3.102 起曾在 CI 为 `TBOX_WEBHOOK_LOG_COMPAT_V1` 提供注释版 `env` 片段（S3.103 已移除）；提案文档曾含 Phase C 准入清单。
> S3.103 起 Phase C：移除 `TBOX_WEBHOOK_LOG_COMPAT_V1` 与 v1-extended `start` 字段；**迁移窗口截止 2026-06-30（UTC 日末）** 后仅保留 canonical 输出。
> S3.104 起扩展 `.gitignore`（`logs/`、`.pytest_cache`、`__pycache__/` 等），减少本地生成物进入 `git status` 未跟踪列表。
> S3.105 起 `docs/WEBHOOK_CONTRACT.md` 与 README 对齐补充 S3.104 `.gitignore` 说明。
> S3.106 起在 `notify` 模块文档与契约 Versioning 明确：`payload_version`（HTTP）≠ `log_version`（校验脚本日志）。
> S3.107 起 `notify` 暴露 `build_tbox_*_payload` 与 `WEBHOOK_TYPE_*`，发送路径复用 builder；pytest 校验顶层键与 `webhook_payload.schema.json` 一致。

## 本地开发

```bash
cd packages/tbox-pipelines
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tbox_pipelines.cli sync --config config/pipeline.sample.json
# optional: export RAGFLOW_AUTO_RUN=false to upload without triggering parse run
```

可选：校验 webhook 示例与 Schema（需 Node 20 与 npm，与 CI 相同；可用 `.node-version` + nvm/fnm/volta 切换）：

```bash
bash scripts/validate_webhook_examples.sh
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
- RBAC 高风险告警使用 `TBOX_RBAC_ALERT_WEBHOOK_URL`，负载类型为 `tbox_rbac_alert`（与同步的 `tbox_sync_summary` 不同）。
- 负载契约与字段说明：**[docs/WEBHOOK_CONTRACT.md](docs/WEBHOOK_CONTRACT.md)**（含 Schema、`curl` 与 **[docs/examples/](docs/examples/)** 示例 JSON）。
