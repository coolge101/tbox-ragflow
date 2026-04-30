# TBOX Pipelines Webhook Contract

HTTP `POST` with `Content-Type: application/json`. All envelopes share top-level fields; interpret by `type`.

`notify.py` also sends **`User-Agent: tbox-pipelines/<version>`** (from installed package metadata, or `tbox-pipelines` if the distribution is not discoverable) on both webhook POSTs so receivers can attribute traffic.

When the envelope `sync_id` is non-empty after trimming, the same value is sent as HTTP header **`X-TBOX-Sync-Id`** (optional for receivers; the JSON body always includes `sync_id`).

Each `send_*` call adds **`Idempotency-Key`** (S3.112): a 64-char lowercase hex **SHA-256** of `payload_type` plus a **canonical JSON** serialization (`sort_keys`, compact separators, `ensure_ascii=True`, **`default=str`** for non-JSON-native values) of the inner dict passed to the builder (`summary` or `rbac_event`). The value is stable for the same logical notification and across transport retries within that call; receivers may use it for deduplication if they support the header.

**Authorization (S3.113):** When configured, `notify.py` sends **`Authorization: Bearer <token>`** on the matching webhook only. Prefer environment variables **`RAGFLOW_NOTIFY_WEBHOOK_BEARER_TOKEN`** and **`TBOX_RBAC_ALERT_WEBHOOK_BEARER_TOKEN`** over JSON secrets in repo files. Do not log token values.

**Log URLs (S3.114):** `webhook_notify_failed` lines pass a **redacted** URL: **query** and **fragment** are stripped, and **`user:pass@`** in `netloc` is replaced with **`***@`**. The real URL is still used for the HTTP `POST`.

**URL allowlist (S3.115 / S3.130):** `send_*` accepts only absolute **`http`** or **`https`** URLs with a non-empty **host** (`netloc`). Other schemes (e.g. `file:`) or host-less URLs are rejected with `webhook_notify_skipped_invalid_url`; no HTTP request is made. Skip logs include a **redacted** `url`, plus `payload_type`, `sync_id`, and `skip_reason=invalid_url`.

**Success observability (S3.116):** After a successful `POST` (`raise_for_status` passes), `notify` emits **`webhook_notify_ok`** at **DEBUG** with **redacted** `url`, **`http_status`**, and **`attempt`/`attempts`** (useful when retries occurred).

**Retries (S3.109 / S3.111 / S3.117 / S3.118 / S3.119 / S3.120 / S3.121 / S3.122 / S3.123 / S3.124 / S3.125 / S3.126 / S3.127 / S3.128 / S3.129 / S3.130 / S3.131 / S3.132 / S3.133 / S3.134 / S3.135 / S3.136 / S3.137 / S3.138 / S3.139 / S3.140):** **408**, **429**, **500**, **502**, **503**, **504**, and transport errors (`httpx.RequestError`) are retried. Base sleep is `retry_backoff_seconds * attempt`. When a transient HTTP response includes `Retry-After`, `notify` accepts either seconds or HTTP-date and sleeps `max(base_backoff, retry_after_seconds)` before the next attempt. Retry warning logs include `log_schema_version`, `outcome=failure`, `delivery_state` (`retrying` or `failed`), `final` (whether this failure ends the send call), `payload_type` (`tbox_sync_summary` / `tbox_rbac_alert`), `sync_id`, `attempt_index`, `attempt_total`, `retry_policy` (`backoff`, `retry_after`, `none`), `retry_eligible` (whether the failure type is retryable), `retries_remaining` (attempts left after current failure), `http_status` (`HTTPStatusError` code or `None`), `retry_after_seconds` (parsed `Retry-After` value when available), `retry_after_source`, `backoff_seconds`, `retry_in_seconds`, `retry_window_ms`, `retry_reason` (standardized values such as `http_429`, `http_non_retryable_403`, `transport_retryable`), `retry_reason_group` (stable coarse bucket: `http_retryable`, `http_non_retryable`, `transport_retryable`, `transport_non_retryable`, `unexpected`), `retry_reason_version` (current taxonomy version, now `1`), `error_class` (Python exception class name), `error_family` (`http`, `transport`, `unexpected`), `attempt_elapsed_ms`, and `total_elapsed_ms` (wall-clock timing for attempt and whole send call). Success logs include `log_schema_version`, `outcome=success`, `delivery_state=delivered`, and the same correlation/timing basics (`payload_type`, `sync_id`, `attempt`, `attempt_index`, `attempt_total`, timing fields). Skip logs include `log_schema_version`, `payload_type`, `sync_id`, `skip_reason`, and redacted `url`. S3.131 adds tests that enforce core-field consistency across success/failure/skip paths. Other HTTP status codes are not retried. `run_sync` passes per-webhook `max_retries` / `retry_backoff_seconds` from `notify_webhook_*` and `rbac_alert_webhook_*` pipeline fields; when omitted they **inherit** the resolved `http_max_retries` / `http_retry_backoff_seconds` (same source as `RagflowClient`: `RAGFLOW_HTTP_MAX_RETRIES` / `RAGFLOW_HTTP_RETRY_BACKOFF_SECONDS` and JSON `http_max_retries` / `http_retry_backoff_seconds`). Override with JSON keys or `RAGFLOW_NOTIFY_WEBHOOK_MAX_RETRIES`, `RAGFLOW_NOTIFY_WEBHOOK_RETRY_BACKOFF_SECONDS`, `TBOX_RBAC_ALERT_WEBHOOK_MAX_RETRIES`, `TBOX_RBAC_ALERT_WEBHOOK_RETRY_BACKOFF_SECONDS`. Library callers of `send_*` may keep defaults (`max_retries=0`) or override.

### Alerting templates (S3.141)

Use `outcome=failure` and `payload_type` as base filters, then route by `delivery_state` and `retry_reason_group`:

1. **Final delivery failures (page-level):**
   - Filter: `delivery_state=failed final=True`
   - Group by: `payload_type`, `retry_reason_group`, `http_status`, `error_class`
   - Purpose: catch notifications that exhausted retry budget or were non-retryable.
2. **Retrying spike (warn-level):**
   - Filter: `delivery_state=retrying final=False`
   - Group by: `payload_type`, `retry_reason_group`
   - Suggested threshold: sudden >3x increase vs previous 15-minute baseline.
3. **Transport instability (infra-level):**
   - Filter: `retry_reason_group=transport_retryable OR retry_reason_group=transport_non_retryable`
   - Group by: `error_class`, `payload_type`
   - Purpose: quickly isolate DNS/TLS/network/connectivity incidents.
4. **Rate-limit pressure (integration-level):**
   - Filter: `retry_reason_group=http_retryable AND http_status=429`
   - Group by: `payload_type`, `sync_id`
   - Purpose: identify receiver-side throttling and decide whether to tune retry/backoff.

Compatibility guidance:
- Prefer `retry_reason_group` for long-lived dashboards and alert routes.
- Use `retry_reason` for drill-down detail only.
- Keep `retry_reason_version` in parser output and branch logic by version only when taxonomy changes.

**Timeouts (S3.110):** `run_sync` passes per-webhook `timeout_seconds` from `notify_webhook_timeout_seconds` / `rbac_alert_webhook_timeout_seconds` in pipeline config (JSON keys or `RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS` / `TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS`; default **10** seconds each, clamped to at least **1**).

## Envelope (all types)

| Field | Type | Description |
|-------|------|-------------|
| `payload_version` | int | Envelope schema version (currently `1`). Receivers may branch on this. |
| `type` | string | Discriminator: `tbox_sync_summary` or `tbox_rbac_alert`. |
| `status` | string | Convenience copy of inner primary status (`summary.status` or `rbac.status`). |
| `sync_id` | string | Correlation id for the run (same as inner when present). |

## `tbox_sync_summary` (business sync)

Configured via `notify_webhook_url` / `RAGFLOW_NOTIFY_WEBHOOK_URL`.

| Field | Type | Description |
|-------|------|-------------|
| `summary` | object | Same shape as one line of `sync_audit.jsonl` / `sync_summary` log: e.g. `sync_id`, `status`, `documents_fetched`, `resolved_dataset_id`, `uploaded_doc_ids`, `run_triggered`, `auto_run_after_upload`, optional RBAC policy metadata when present, etc. |

Notification policy: failures always eligible; success only if `notify_on_success` is true.

## `tbox_rbac_alert` (RBAC high-risk)

Configured via `rbac_alert_webhook_url` / `TBOX_RBAC_ALERT_WEBHOOK_URL`. Only sent for high-risk failed RBAC events (see `TBOX_RBAC_ALERT_HIGH_RISK_REASONS`), after dedupe rules.

| Field | Type | Description |
|-------|------|-------------|
| `rbac` | object | RBAC event: `sync_id`, `status`, `reason`, `actor_role`, optional `error`, policy fields (`rbac_policy_source`, `rbac_policy_fingerprint`, `rbac_policy_version`, `rbac_policy_release_tag`), and when applicable `rbac_alert_suppressed_in_window` (count of suppressed alerts since last emit for the same dedupe key). |

## JSON Schema (machine-readable)

Canonical schema (Draft 07 `oneOf` for the two payload shapes):

- [`webhook_payload.schema.json`](webhook_payload.schema.json)

Validate locally (requires Node/npm; uses [ajv-cli](https://www.npmjs.com/package/ajv-cli) via `npx --yes`). Use Node **20** to match CI (this package ships [`.node-version`](../.node-version) for nvm/fnm/volta). From `packages/tbox-pipelines`:

```bash
bash scripts/validate_webhook_examples.sh
```

### CI

The `tbox-pipelines` GitHub Actions job runs `bash scripts/validate_webhook_examples.sh` (Node 20), which validates **every** `docs/examples/*.sample.json` against the schema. See `.github/workflows/ci.yml` at the repository root. If you change `webhook_payload.schema.json` or add or edit samples under `docs/examples/`, keep them in sync or CI will fail.

`pytest` also checks that [`webhook_payload.schema.json`](webhook_payload.schema.json) parses as JSON, still declares Draft-07 `oneOf` and `definitions` (including `envelope`), derives the expected payload `type` set from `oneOf` `$ref` targets (so it stays aligned with the schema file), asserts each payload definition's `properties.type.const` matches that definition's name, and loads the same `*.sample.json` files for a small envelope smoke check (`payload_version`, `type`, `status`, `sync_id`, the nested body object keyed per `definitions.<type>.allOf[].required` (e.g. `summary` / `rbac`), matching inner `sync_id` / `status` via direct equality (inner `status` and `sync_id` keys must exist in examples), exact top-level key set = envelope keys + current nested body key, with `payload_version` being a strict JSON integer (not boolean), non-empty/trimmed `sync_id`/`status` strings (no leading/trailing whitespace), non-empty inner object with non-blank string keys, no extra nested body key for other payload types, filename stem vs `type`, and one sample file per schema payload type), all without Node. In CI, that job runs **before** the Node/`ajv-cli` step so obvious breaks fail without downloading the validator.

## Example payload files

Checked-in copies you can send or validate as-is. Keep **one** `<type>.sample.json` per payload `type` declared in the schema root `oneOf`; `pytest` enforces the filename set matches those `$ref` targets.

| File | `type` |
|------|--------|
| [`examples/tbox_sync_summary.sample.json`](examples/tbox_sync_summary.sample.json) | `tbox_sync_summary` |
| [`examples/tbox_rbac_alert.sample.json`](examples/tbox_rbac_alert.sample.json) | `tbox_rbac_alert` |

Add new webhook shapes under `docs/examples/` as `<type>.sample.json` only (the basename without `.sample.json` must equal envelope `type`, checked in `pytest`); other filenames in that directory are not validated by `scripts/validate_webhook_examples.sh`.

Keep top-level `sync_id` equal to `summary.sync_id` / `rbac.sync_id`, and top-level `status` equal to `summary.status` / `rbac.status` in checked-in examples (direct equality; no fallback branch in the sample tests). Checked-in examples use non-empty and trimmed `sync_id`/`status` (no leading/trailing whitespace) on the envelope and inside `summary` / `rbac` (mirrors real audit payloads), and keep exact top-level keys to envelope fields + the matching nested body key (with no nested body key for other payload types), plus a non-empty nested object whose keys are non-blank strings (`pytest` checks both).

## Example `curl` (from `packages/tbox-pipelines`)

### `tbox_sync_summary`

```bash
curl -sS -X POST "$RAGFLOW_NOTIFY_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @docs/examples/tbox_sync_summary.sample.json
```

### `tbox_rbac_alert`

```bash
curl -sS -X POST "$TBOX_RBAC_ALERT_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @docs/examples/tbox_rbac_alert.sample.json
```

## Versioning

- HTTP POST bodies use **`payload_version`** on the JSON envelope (`WEBHOOK_PAYLOAD_VERSION` in `notify.py`). Do not confuse this with **`log_version`** on `validate_webhook_examples.sh` stdout JSON log lines (validator/CI only; currently **`2`**). **HTTP 负载**与校验脚本 **`log_version`** 无关，请勿混用。
- Increment `WEBHOOK_PAYLOAD_VERSION` in `tbox_pipelines/notify.py` when adding required envelope fields or changing meaning of `type` values.
- Prefer additive changes inside `summary` / `rbac` without bumping envelope version when possible.
- When `payload_version` or required envelope keys change, update `webhook_payload.schema.json` and the `docs/examples/*.sample.json` files (CI validates all of them).
- For each payload definition under `definitions`, keep `properties.type.const` equal to the definition name (and to envelope `type`); `pytest` checks this.
- Runtime envelopes are built by `notify.build_tbox_sync_summary_payload` / `notify.build_tbox_rbac_alert_payload` (and `send_*` wrappers). `pytest` asserts their top-level key sets match schema-derived inner keys (`tests/test_webhook_example_files.py`).

> S3.30 起 `scripts/validate_webhook_examples.sh` 从 `packages/tbox-pipelines/.node-version` 读取目标 Node 主版本，并要求本地 Node >= 该主版本（CI uses Node 20）。
> S3.31 起 `validate_webhook_examples.sh` 会检查本地 `npx` 是否可用（缺失则提示安装 npm/Node）。
> S3.32 起 CI 的 `actions/setup-node` 使用 `packages/tbox-pipelines/.node-version` 读取 Node 版本，避免与脚本/文档版本漂移。
> S3.33 起脚本在缺失/解析失败时默认 required Node major=20，并给出明确提示。
> S3.34 起 `validate_webhook_examples.sh` 会对 `docs/examples/*.sample.json` 排序，输出/执行顺序更确定。

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
> S3.102 起曾在 CI workflow 中为 `TBOX_WEBHOOK_LOG_COMPAT_V1` 提供注释版 `env` 示例（**S3.103 已移除**）；`S3.75-S3.100-field-consolidation-proposal.md` 曾补充 Phase B 说明与 Phase C 准入清单。
> S3.103 起 Phase C：`TBOX_WEBHOOK_LOG_COMPAT_V1` 及 v1-extended `start` 字段已移除；**迁移窗口截止 `2026-06-30`（UTC 日末）**，此后脚本仅输出 canonical `start` JSON。
> S3.104 起扩展 `packages/tbox-pipelines/.gitignore`（`logs/`、`.pytest_cache`、`__pycache__/` 等），减少本地生成物干扰 `git status` 与提交审阅（与 README 变更日志一致）。
> S3.105 起在本文 Versioning 与 README 对齐补充：S3.104 `.gitignore` 说明（文档/变更日志一致）。
> S3.106 起在 `notify.py` 模块文档与 Versioning 节明确：**HTTP 负载 `payload_version`** 与 **校验脚本 stdout `log_version`**（当前 `2`）无关，避免混用。
> S3.107 起 `notify` 提供 `build_tbox_sync_summary_payload` / `build_tbox_rbac_alert_payload` 与 `WEBHOOK_TYPE_*` 常量；`send_*` 复用 builder；`pytest` 将 builder 顶层键与 schema 推导的内层键对齐。
> S3.108 起 `notify` 的 webhook `POST` 增加 `User-Agent: tbox-pipelines/<version>`（不可解析时为 `tbox-pipelines`），便于接收端日志归因。
> S3.109 起非空 `sync_id` 时增加请求头 `X-TBOX-Sync-Id`；`run_sync` 将 `http_max_retries` / `http_retry_backoff_seconds` 传入 webhook，对网络错误与 408/429/5xx 可重试状态做有限次重试。
> S3.110 起 `run_sync` 传入 `notify_webhook_timeout_seconds` / `rbac_alert_webhook_timeout_seconds`（JSON 或 `RAGFLOW_NOTIFY_WEBHOOK_TIMEOUT_SECONDS`、`TBOX_RBAC_ALERT_WEBHOOK_TIMEOUT_SECONDS`，默认 10s、下限 1s）。
> S3.111 起 webhook 重试次数与退避可独立于 RAGFlow HTTP：`notify_webhook_max_retries` 等四字段 / 对应 `RAGFLOW_NOTIFY_*`、`TBOX_RBAC_ALERT_WEBHOOK_*` env；未设置时继承已解析的 `http_max_retries` / `http_retry_backoff_seconds`。
> S3.112 起 `notify` 为每次 `send_*` 生成 `Idempotency-Key`（64 位 hex SHA-256，见契约正文），同一调用内重试保持不变。
> S3.113 起可选 `Authorization: Bearer`（`notify_webhook_bearer_token` / `rbac_alert_webhook_bearer_token` 或对应 env）；幂等键 JSON 序列化使用 `default=str`。
> S3.114 起 `webhook_notify_failed` 日志中的 `url` 为脱敏形式（去掉 query/fragment，`user:pass@` → `***@`）。
> S3.115 起仅允许绝对 `http`/`https` 且含 host 的 webhook URL；否则记录 `webhook_notify_skipped_invalid_url` 并不发起请求。
> S3.116 起成功投递后打 `webhook_notify_ok`（DEBUG，脱敏 `url`、`http_status`、`attempt/total`）。
> S3.117 起 webhook 可重试 HTTP 失败若带 `Retry-After` 秒值，则重试等待采用 `max(retry_backoff_seconds * attempt, Retry-After)`；无效/缺失时回退到原退避。
> S3.118 起 `Retry-After` 额外支持 HTTP-date（除秒值外），统一折算后仍采用 `max(线性退避, Retry-After)`。
> S3.119 起 `webhook_notify_failed` 增加 `retry_in_seconds` 字段，记录下一次重试前实际等待时长（不重试时为 `None`）。
> S3.120 起 `webhook_notify_failed` 增加 `retry_policy`（`backoff` / `retry_after` / `none`），便于区分重试等待来源。
> S3.121 起 `webhook_notify_failed` 增加 `retry_after_seconds`（成功解析时为秒数，否则为 `None`），便于观察服务端 `Retry-After` 对重试的影响。
> S3.122 起 `webhook_notify_failed` 增加 `retry_reason`（如 `request_error`、`http_status_429`、`http_status_non_retryable`），便于按失败类型聚合告警。
> S3.123 起 `webhook_notify_failed` 增加 `http_status`（HTTP 异常时记录状态码，否则为 `None`），便于直接按状态码检索失败日志。
> S3.124 起 `webhook_notify_failed` 增加 `retries_remaining`（当前失败后剩余重试次数），便于快速判断是否接近重试上限。
> S3.125 起 `webhook_notify_failed` 增加 `retry_eligible`（失败类型本身是否可重试），与 `retry`（当前是否会继续重试）配合更清晰。
> S3.126 起 `webhook_notify_ok` / `webhook_notify_failed` 均增加 `payload_type`，便于按 webhook 类型做日志分流与聚合。
> S3.127 起 `webhook_notify_ok` / `webhook_notify_failed` 均增加 `sync_id`，便于与同步任务日志直接关联排障。
> S3.128 起 `webhook_notify_ok` / `webhook_notify_failed` 均增加 `attempt_elapsed_ms` 与 `total_elapsed_ms`，支持按耗时维度观测 webhook 投递表现。
> S3.129 起日志语义统一：`webhook_notify_ok` 增加 `outcome=success`，`webhook_notify_failed` 增加 `outcome=failure` 与 `final`，便于区分重试中失败与最终失败。
> S3.130 起 `webhook_notify_skipped_invalid_url` 增加 `payload_type`、`sync_id`、`skip_reason=invalid_url`，让“跳过路径”与成功/失败日志具备一致关联上下文。
> S3.131 起新增 notify 日志一致性测试，约束 success/failure/skip 三条路径核心字段持续齐全，降低后续字段回归风险。
> S3.132 起 success/failure 日志新增 `attempt_index` 与 `attempt_total`（保留原 `attempt=x/y`），便于机器消费与指标聚合。
> S3.133 起新增 `delivery_state`：成功为 `delivered`，失败为 `retrying`/`failed`，让告警规则可直接按终态分流。
> S3.134 起 success/failure/skip 三路径统一增加 `log_schema_version`（当前 `1`），便于日志解析器按版本演进。
> S3.135 起 failure 日志增加 `error_class`（异常类名），便于告警与统计按异常类型聚合。
> S3.136 起 failure 日志增加 `error_family`（`http`/`transport`/`unexpected`），便于聚合规则稳定分组。
> S3.137 起将重试计算抽为 `_webhook_retry_decision`，并增加 `retry_after_source`、`backoff_seconds`、`retry_window_ms` 与表驱动测试，统一重试诊断语义。
> S3.138 起 `retry_reason` 标准化为稳定枚举（如 `http_429`、`http_non_retryable_403`、`transport_retryable`），减少规则匹配歧义。
> S3.139 起 failure 日志新增 `retry_reason_version=1`，为后续重试原因枚举升级提供兼容锚点。
> S3.140 起 failure 日志新增 `retry_reason_group`（粗粒度稳定分组），便于告警规则按大类聚合并降低枚举变动影响。
> S3.141 起补充基于 `retry_reason_group` 的告警模板，明确 `failed`/`retrying` 分流与稳定聚合建议。

## Field Consolidation (Phase A)

S3.75-S3.100 的 `start` 日志字段已进入压缩治理阶段。Phase A 曾**文档标记**下列字段为 deprecated（历史列表；**S3.103 起不再出现在 `start` 输出中**）。

提案文档见：[`S3.75-S3.100-field-consolidation-proposal.md`](S3.75-S3.100-field-consolidation-proposal.md)

历史 deprecated 名（已移除，勿再依赖）：

- `validator_command_source`
- `validator_invocation`
- `validator_auto_install`
- `sample_result_status_field`
- `sample_total_field`
- `sample_path_field`
- `sample_type_field`
- `samples_glob_applied`
- `samples_sorted`
- `samples_nonempty`
- `sample_count_expected`
- `samples_bytes_computed`
- `schema_exists`
- `schema_hash_verified`

## Field Consolidation (Phase B)（历史）

Phase B 曾实现“默认 canonical + 可选 `TBOX_WEBHOOK_LOG_COMPAT_V1`”。**S3.103 / Phase C 已删除兼容开关**；若你仍依赖上述扩展字段，须在 **2026-06-30（UTC）** 前改为只解析 canonical 字段集（见 `tests/test_validate_webhook_log_contract.py` 与脚本内 `start_json`）。

## Field Consolidation (Phase C)

- **迁移截止日**：`2026-06-30`（UTC，含当日）——对外承诺的 v1-extended / compat **语义支持终点**；依赖方须在此前改为只解析 canonical `start`。
- **行为**：`validate_webhook_examples.sh` 的 `start` 行仅包含 canonical 键；环境变量 `TBOX_WEBHOOK_LOG_COMPAT_V1` **已删除**，设置与否均无效果。
- **PR 做法**：单 PR 合并脚本、契约测试、CI 注释与本文档；PR 描述中写明截止日与破坏性变更范围。
- **合并时间与 review**：本分支已含删除实现，便于提前 review；若组织要求「代码删除不得早于日历截止日」，可将 **计划合并日** 安排在 `2026-06-30` 之后，再发补丁 release（流程由维护者定）。
