# TBOX Pipelines Webhook Contract

HTTP `POST` with `Content-Type: application/json`. All envelopes share top-level fields; interpret by `type`.

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

- Increment `WEBHOOK_PAYLOAD_VERSION` in `tbox_pipelines/notify.py` when adding required envelope fields or changing meaning of `type` values.
- Prefer additive changes inside `summary` / `rbac` without bumping envelope version when possible.
- When `payload_version` or required envelope keys change, update `webhook_payload.schema.json` and the `docs/examples/*.sample.json` files (CI validates all of them).
- For each payload definition under `definitions`, keep `properties.type.const` equal to the definition name (and to envelope `type`); `pytest` checks this.

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
