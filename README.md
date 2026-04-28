# TBOX RAGFlow Platform

基于 RAGFlow 的 TBOX 知识库工程：**上游源码** + **覆盖层（overlay）** + **独立流水线包** + **Docker 编排**。

## S0（Harness / 工程化骨架）

- 文档骨架：`docs/README.md`、`docs/01-requirements.md`、`docs/02-architecture-outline.md`、`docs/reviews/phase-S0-review.md`
- 协作：`CONTRIBUTING.md`、`.github/pull_request_template.md`
- 最小 CI：`.github/workflows/ci.yml`（仅 `packages/tbox-pipelines`，不拉内网、无密钥）
- Cursor 规则：`.cursor/rules/tbox-harness.mdc`

## 目录说明

| 路径 | 说明 |
|------|------|
| `upstream/ragflow/` | RAGFlow 源码副本（从原仓库 rsync，含 `.git`）。升级官方版本时在此目录 merge/rebase。 |
| `apps/ragflow-server/overlay/` | 打进镜像的差量文件（目录结构与 RAGFlow 仓库内一致，如 `api/...`）。 |
| `apps/ragflow-server/Dockerfile` | 在官方镜像之上叠加 `overlay/`（快速出包）。完整从源码构建见下文。 |
| `packages/tbox-pipelines/` | 建库 ETL、调用 RAGFlow API 等，可单独打成 worker 镜像。 |
| `deploy/` | 对外使用的 `docker-compose` 与示例环境变量。 |
| `patches/` | 可选：对 `upstream/ragflow` 的 `git apply` 补丁。 |
| `scripts/` | 同步上游、打补丁等脚本。 |

## 在 Cursor 中打开本工程

**文件 → 打开文件夹**，选择平台根目录 `tbox-ragflow-platform/`（与 `upstream/`、`apps/` 同级）。

本仓库当前生成位置（在 RAGFlow 工作区内时）：

```text
/home/vboxuser/ragflow/tbox-ragflow-platform
```

你也可以将整个 `tbox-ragflow-platform` 目录**剪切**到任意路径后再打开；此时同步上游请设置 `RAGFLOW_SRC` 指向 RAGFlow 源码根目录（见 `scripts/resync-upstream.sh`）。

## 同步上游目录（推荐本地再执行一次）

首次拷贝若被中断或需与当前仓库对齐，在项目根执行：

```bash
./scripts/resync-upstream.sh
```

## 构建带 TBOX 覆盖的 RAGFlow 镜像

在项目根 `tbox-ragflow-platform/` 执行：

```bash
docker build -f apps/ragflow-server/Dockerfile -t tbox-ragflow:local .
```

## 完整栈（依赖 + RAGFlow）

默认镜像名在 `deploy/docker-compose.yml` 中定义。也可直接使用上游自带编排：

```bash
cd upstream/ragflow/docker
docker compose -f docker-compose.yml up -d
```

将其中 `ragflow` 服务的镜像替换为 `tbox-ragflow:local` 即可接入你的 overlay 构建产物（按需合并进 `deploy/docker-compose.yml`）。

## 从源码构建（不用官方预置镜像）

在 `upstream/ragflow` 目录按官方 `Dockerfile` 构建（需满足官方文档中的 BuildKit 等条件）：

```bash
cd upstream/ragflow
docker build --platform linux/amd64 -f Dockerfile -t tbox-ragflow:from-src .
```

TBOX 二开仍建议优先用 `overlay/` 或 `patches/` 保持差量可审。
