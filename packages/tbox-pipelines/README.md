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
  - `RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS` (default `10`, minimum `1`; per-request `httpx` timeout for sync-summary webhook)
  - `RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES` (default: inherit `RAGFLOW_HTTP_MAX_RETRIES` / JSON `http_max_retries` after merge)
  - `RAGFLOW_NOTIFY_WEBHOOK_RETRY_BACKOFF_SECONDS` (default: inherit `RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS` / JSON `http_retry_backoff_seconds`)
  - `TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS` (default `10`, minimum `1`; RBAC alert webhook)
  - `TBOX_RBAC_ALERT_WEBHOOK_MAX_RETRIES` (default: inherit HTTP retry settings)
  - `TBOX_RBAC_ALERT_WEBHOOK_RETRY_BACKOFF_SECONDS` (default: inherit HTTP retry backoff)
  - `RAGFLOW_NOTIFY_WEBHOOK_BEARER_TOKEN` (optional; `Authorization: Bearer` for sync-summary webhook only; prefer env over committing secrets to JSON)
  - `TBOX_RBAC_ALERT_WEBHOOK_BEARER_TOKEN` (optional; RBAC alert webhook only)
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
> S3.106 起在 `notify.py` 与 `WEBHOOK_CONTRACT.md` 明确区分：**HTTP 负载 `payload_version`** 与 **校验脚本 stdout `log_version`**（当前 `2`），避免混用。
> S3.107 起 `notify` 暴露 `build_tbox_*_payload` 与 `WEBHOOK_TYPE_*`，发送路径复用 builder；pytest 校验顶层键与 `webhook_payload.schema.json` 一致。
> S3.108 起 webhook `POST` 带 `User-Agent: tbox-pipelines/<version>`（见 `docs/WEBHOOK_CONTRACT.md`）。
> S3.109 起 webhook 带 `X-TBOX-Sync-Id`（`sync_id` 非空时）；`run_sync` 复用 `RAGFLOW_HTTP_MAX_RETRIES` / `RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS` 对可瞬时失败重试（与 `RagflowClient` 一致，见契约文档）。
> S3.110 起 `notify_webhook_timeout_seconds` / `rbac_alert_webhook_timeout_seconds` 可经 JSON 或 `RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS`、`TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS` 配置（默认 `10`，下限 `1` 秒）。
> S3.111 起 webhook 重试与退避可独立配置（`notify_webhook_max_retries` 等 JSON 与 `RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES` 等 env）；未配置时继承合并后的 `http_max_retries` / `http_retry_backoff_seconds`（见 `docs/WEBHOOK_CONTRACT.md`）。
> S3.112 起 webhook `POST` 带 `Idempotency-Key`（SHA-256，见 `docs/WEBHOOK_CONTRACT.md`），便于接收端去重。
> S3.113 起可选 Bearer：`RAGFLOW_NOTIFY_WEBHOOK_BEARER_TOKEN` / `TBOX_RBAC_ALERT_WEBHOOK_BEARER_TOKEN`（或 JSON 字段，不推荐入库）；幂等键序列化对非 JSON 原生值使用 `default=str`。
> S3.114 起 webhook 失败日志中的 URL 脱敏（无 query/fragment，掩码 `user:pass@`），见 `docs/WEBHOOK_CONTRACT.md`。
> S3.115 起 webhook URL 仅允许绝对 `http`/`https`（含 host）；`file:` 等 scheme 会被拒绝并打脱敏告警日志。
> S3.116 起 webhook 成功后在 DEBUG 记录 `webhook_notify_ok`（脱敏 URL、HTTP 状态、尝试序号），见 `docs/WEBHOOK_CONTRACT.md`。
> S3.117 起 webhook 可重试 HTTP 失败若返回 `Retry-After`（秒值），重试等待采用 `max(线性退避, Retry-After)`；无效/缺失时回退原 `retry_backoff_seconds * attempt`。
> S3.118 起 `Retry-After` 额外支持 HTTP-date（不仅秒值）；折算后仍采用 `max(线性退避, Retry-After)`。
> S3.119 起 `webhook_notify_failed` 增加 `retry_in_seconds`（下一次重试前实际等待秒数；不重试时为 `None`），便于排障与日志聚合。
> S3.120 起 `webhook_notify_failed` 增加 `retry_policy`（`backoff`/`retry_after`/`none`），用于标识重试等待来源。
> S3.121 起 `webhook_notify_failed` 增加 `retry_after_seconds`（解析到 `Retry-After` 时记录秒值），便于判断服务端限流提示是否生效。
> S3.122 起 `webhook_notify_failed` 增加 `retry_reason`（如 `request_error`、`http_status_429`、`http_status_non_retryable`），便于按失败类型做日志聚合。
> S3.123 起 `webhook_notify_failed` 增加 `http_status`（HTTP 异常时记录状态码），便于直接按状态码统计失败分布。
> S3.124 起 `webhook_notify_failed` 增加 `retries_remaining`（当前失败后剩余重试次数），便于快速识别接近重试上限的告警。
> S3.125 起 `webhook_notify_failed` 增加 `retry_eligible`（失败类型本身是否可重试），帮助区分“可重试但已无剩余次数”与“本质不可重试”。
> S3.126 起 `webhook_notify_ok` / `webhook_notify_failed` 增加 `payload_type`，便于按 webhook 类型做日志聚合。
> S3.127 起 `webhook_notify_ok` / `webhook_notify_failed` 增加 `sync_id`，便于与同步任务日志关联排障。
> S3.128 起 `webhook_notify_ok` / `webhook_notify_failed` 增加 `attempt_elapsed_ms` 和 `total_elapsed_ms`，便于定位慢请求与累计重试耗时。
> S3.129 起日志统一增加 `outcome`（success/failure），并在失败日志增加 `final`（是否最终失败），便于告警分级与筛选。
> S3.130 起无效 URL 跳过日志 `webhook_notify_skipped_invalid_url` 增加 `payload_type`、`sync_id`、`skip_reason=invalid_url`，实现成功/失败/跳过三条路径一致上下文。
> S3.131 起新增日志一致性测试，校验 success/failure/skip 三条路径核心上下文字段持续齐全，减少后续重构回归。
> S3.132 起 success/failure 日志新增结构化重试序号字段 `attempt_index`、`attempt_total`（同时保留 `attempt=x/y` 兼容旧检索）。
> S3.133 起 success/failure 日志新增 `delivery_state`（`delivered`/`retrying`/`failed`），便于告警按终态直接分组。
> S3.134 起 success/failure/skip 日志新增 `log_schema_version`（当前 `1`），为后续日志字段演进提供兼容锚点。
> S3.135 起 failure 日志新增 `error_class`（如 `HTTPStatusError`、`ConnectError`），便于按异常类别统计与告警。
> S3.136 起 failure 日志新增 `error_family`（`http`/`transport`/`unexpected`），便于建立稳定的异常分组看板与告警规则。
> S3.137 起重试决策统一收敛到 helper，并新增 `retry_after_source`、`backoff_seconds`、`retry_window_ms`，配套表驱动测试覆盖关键组合。
> S3.138 起将 `retry_reason` 标准化为稳定枚举（如 `http_429`、`http_non_retryable_403`、`transport_retryable`），降低告警规则分支复杂度。
> S3.139 起 failure 日志新增 `retry_reason_version`（当前 `1`），为 retry reason taxonomy 迭代提供兼容锚点。
> S3.140 起 failure 日志新增 `retry_reason_group`（粗粒度稳定分组），便于告警按大类聚合，减少对细粒度枚举的耦合。
> S3.141 起 `WEBHOOK_CONTRACT` 增加基于 `retry_reason_group` 的告警模板与分流建议，便于快速落地监控规则。
> S3.142 起新增 `docs/examples/webhook_alert_rules.sample.md`（可复制的告警规则示例），并在 `WEBHOOK_CONTRACT` 建立引用。
> S3.143 起新增 `docs/examples/webhook_alert_rules.datadog.sample.md`（Datadog 查询语法样例），便于直接创建平台监控。
> S3.144 起新增 `docs/examples/webhook_alert_rules.promql.sample.md`（Loki/Prometheus 风格样例），补齐开源观测栈落地模板。
> S3.145 起新增 `docs/examples/webhook_alert_rules.openobserve.sample.md`（OpenObserve 查询语法样例），扩展轻量日志平台落地参考。
> S3.146 起新增 `docs/examples/webhook_alert_rules.elasticsearch.sample.md`（Elasticsearch/KQL 风格样例），补充 ELK 生态落地模板。
> S3.147 起新增 `docs/examples/webhook_alert_rules.index.md`（样例总索引 + 字段映射速查），便于跨平台统一落地。
> S3.148 起新增 `webhook_alert_rules.migration_checklist.md` 与 `webhook_alert_rules.troubleshooting.md`，形成告警规则落地与排障闭环文档。
> S3.149 起新增 `docs/examples/webhook_alerting_runbook.md`（平台无关告警运维 SOP），覆盖分级响应、交接与复盘模板。
> S3.150 起新增 `docs/examples/webhook_alerting_baseline.md`（告警治理基线包），统一阈值、分环境策略、抑制与升级策略。
> S3.151 起新增 `docs/examples/webhook_alerting_baseline.parameterized.md`（critical/non-critical 参数化模板），支持快速套用治理基线。
> S3.152 起新增 `docs/examples/webhook_alerting_monitor_as_code.template.yaml`（通用 monitor-as-code 模板），支持从参数化基线渲染平台规则。
> S3.153 起新增 `webhook_alerting_monitor_as_code.datadog.rendered.yaml` 与 `webhook_alerting_monitor_as_code.prometheus.rendered.yaml`，提供即用型平台渲染样例。
> S3.154 起新增 `webhook_alerting_render_spec.md` 与 `webhook_alerting_render_acceptance_checklist.md`，固化渲染一致性规范与合并门禁。
> S3.155 起新增 `webhook_alerting_render_change_log.template.md` 与 `webhook_alerting_render_change_log.sample.md`，规范渲染变更审计记录。
> S3.156 起新增 `docs/examples/README.md`（examples 总览与维护约定），提升多人协作下的文档可维护性。
> S3.157 起新增 `scripts/validate_alert_docs_links.py`（含测试），为 examples 文档关键互链提供自动自检门禁。
> S3.158 起将 `validate_alert_docs_links.py` 纳入 CI（并覆盖 `scripts` 的 Ruff 检查），同时标准化失败输出格式，便于快速定位缺链。
> S3.159 起扩展 docs-link gate，新增 README/WEBHOOK_CONTRACT 的关键 S3 changelog 证据一致性检查，减少跨文档演进漂移。
> S3.160 起引入 `docs/examples/alert_docs_gate_rules.json`，将 gate 规则配置化，便于后续按阶段增量维护。
> S3.161 起新增 `docs/examples/alert_docs_gate_rules.schema.json`，并在 gate 运行时执行规则 schema 校验，提升配置可靠性。
> S3.162 起新增 `docs/examples/gate_rules_invalid/` 负例样本并纳入 gate 测试，提升失败路径回归保障。
> S3.163 起新增 gate `--verbose` 诊断模式与测试，输出规则加载/检查摘要，提升 CI 失败排障效率。
> S3.164 起 CI 中 docs gate 默认开启 `--verbose`，并使用日志分组输出，便于快速浏览与定位问题。
> S3.165 起 gate 成功态增加结构化 summary 输出（单行 JSON），为 CI 健康度指标采集提供稳定锚点。
> S3.166 起 gate summary 增加 `summary_version=1`，为后续摘要字段演进提供兼容能力。
> S3.167 起 CI 增加 gate summary 解析与固定计数回显（`alert_docs_gate_metrics`），便于日志检索和指标采集。
> S3.169 起将 gate summary 字段白名单配置化（`summary_contract.metric_keys`），使输出字段集由 `alert_docs_gate_rules.json` 驱动并受 schema 约束。
> S3.170 起将 CI 的 `alert_docs_gate_metrics` 提取下沉到独立脚本 `emit_alert_docs_gate_metrics.py`，按 summary 动态字段输出，减少 workflow 内联脚本引号/语法风险。
> S3.171 起 `emit_alert_docs_gate_metrics.py` 强制校验 `summary_contract`（event/version/metric_keys），并拒绝未知或缺失指标键，保证 CI 回显与契约一致。
> S3.172 起 metrics emitter 支持 `--emit-json` 输出 `alert_docs_gate_metrics_json` 镜像行，CI 同时回显 kv 与 JSON 两种格式，便于后续机器采集。
> S3.173 起 metrics emitter 强制 `metric_keys` 对应值为非负整数；负值、布尔值或字符串等非法值会直接失败，避免异常计数污染监控指标。
> S3.174 起 metrics emitter 支持 `--write-github-output`：在 CI 将 kv 行、JSON 镜像行与纯 JSON 负载写入 `GITHUB_OUTPUT`，并在 workflow job 上暴露 `alert_docs_gate_metrics_*` outputs，便于后续 job 或调用方消费。
> S3.175 起 metrics emitter 支持 `--write-step-summary`：在存在 `GITHUB_STEP_SUMMARY` 时追加 Markdown 指标表；CI 新增 `alert-docs-gate-consumer` job，通过 `needs.tbox-pipelines.outputs.alert_docs_gate_metrics_json` 校验跨 job outputs 传递。
> S3.176 起在 `alert_docs_gate_rules.json` 增加 `metrics_emit_contract.emit_version`，metrics 的 kv/JSON/Step Summary/`GITHUB_OUTPUT` 均携带 `metrics_emit_version` 字段，便于与 gate `summary_version` 解耦演进。
> S3.177 起新增 `docs/examples/alert_docs_gate_metrics_payload.schema.json`，对 CI metrics JSON **metrics payload** 做结构契约；`emit_alert_docs_gate_metrics.py` 发出前校验，避免字段漂移污染下游 job。
> S3.178 起将 metrics schema 校验下沉到可复用模块 `tbox_pipelines.alert_docs_gate_metrics_schema`，新增独立 CLI `scripts/validate_alert_docs_metrics_payload.py`（stdin 或 `--payload-path`）；CI `alert-docs-gate-consumer` 通过该脚本校验跨 job `alert_docs_gate_metrics_json` 输出，与 emitter 共用同一套 Draft-07 子集逻辑。
> S3.179 起将校验 CLI 实现迁入 `tbox_pipelines.metrics_payload_validate_cli`，在 `pyproject.toml` 注册控制台入口 `validate-alert-docs-metrics-payload`；consumer job 使用该命令；仓库内 `scripts/validate_alert_docs_metrics_payload.py` 保留为薄包装以便未安装包时 `PYTHONPATH=src` 直跑。
> S3.180 起将 metrics 发射逻辑迁入 `tbox_pipelines.metrics_emit_cli`，注册 `emit-alert-docs-gate-metrics`；CI docs gate 步骤改用该入口；`scripts/emit_alert_docs_gate_metrics.py` 保留薄包装。
> S3.181 起将 docs 互链门禁迁入 `tbox_pipelines.alert_docs_links_validate_cli`，注册 `validate-alert-docs-links`；CI gate 第一步改用该入口；`scripts/validate_alert_docs_links.py` 保留薄包装；亦可用 `python -m tbox_pipelines.alert_docs_links_validate_cli`。
> S3.182 起新增统一入口 `alert-docs-gate`（`tbox_pipelines.alert_docs_gate_cli`）：`ci` 子命令在进程内串联「校验 stdout + tee 写日志」与 metrics emit，替代 shell 管道；`validate` 子命令等价于 `validate-alert-docs-links`；CI 主 job 的 gate 步骤合并为单条 `alert-docs-gate ci ...`。
> S3.183 起 `alert-docs-gate` 增加 `metrics-validate` 子命令（等价 `validate-alert-docs-metrics-payload`）；CI `alert-docs-gate consumer` job 对 job output 改为 `alert-docs-gate metrics-validate`，与主 job 共用同一入口名。
> S3.184 起支持 `alert-docs-gate emit ...`：将 `emit` 之后的 **argv** 原样交给 `metrics_emit_cli`（与 `emit-alert-docs-gate-metrics` 一致），便于在统一入口名下拼接与 `ci` 不同的 emit 参数。
> S3.185 起抽取 `_invoke_emit_cli` 供 `ci` 第二阶段与 `emit` 转发共用；新增 `alert-docs-gate version` 子命令，通过 **importlib.metadata** 打印 `tbox-pipelines` 发行版本。
> S3.186 起以 `_invoke_cli_argv` 统一各 **subcommand** 对下游 CLI `main()` 的 `sys.argv` 切换；`validate`、`metrics-validate`、`emit`（经 `_invoke_emit_cli`）与 `ci` 校验阶段共用同一套保存/恢复逻辑。
> S3.187 起 CI 在 `::group::alert-docs-gate` 日志组内、执行 `alert-docs-gate ci` 之前先跑 `alert-docs-gate version`，将 **tbox-pipelines** 发行版写入 job 日志便于排障对齐。
> S3.188 起 `alert-docs-gate-consumer` job 在 `::group::alert-docs-gate-consumer` 组内、`metrics-validate` 前同样打印 `alert-docs-gate version`；`packages/tbox-pipelines/.gitignore` 增加 **uv.lock** 以忽略本地 `uv` 试跑误生成文件。
> S3.189 起新增 `alert-docs-gate commands` 子命令，单行列出 argparse **subcommand**（`emit` 单独标注为 **pre-argparse** 转发，与 `ci`/`validate` 等并列说明）。
> S3.190 起 CI 在主 job 与 `alert-docs-gate-consumer` 的 gate 日志组内，于 `alert-docs-gate version` 之后追加 `alert-docs-gate commands`，作为 **CI diagnostics** 输出固定摘要行。
> S3.168 起新增 gate 指标断言测试，确保 summary JSON 的关键字段集合与类型稳定。

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
