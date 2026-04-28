# 01 需求说明（阶段化）

> **当前阶段**：S1 — ingest skeleton（爬取与入库最小骨架）  
> **权威基线**：[TBOX-RAGFlow-知识库项目基线与Harness约定.md](./TBOX-RAGFlow-知识库项目基线与Harness约定.md)

## 工程决策（已确认）

| 项 | 结论 | 确认日期 |
|----|------|----------|
| GitHub 仓库形态 | **独立仓库**：以本目录 `tbox-ragflow-platform` 为远端根仓（`.github/workflows` 位于本仓根） | 2026-04-28 |
| 默认主干分支 | **`main`** | 2026-04-28 |
| S0 完成定义 | **文档 + 最小 CI + 可复现的 `tbox-ragflow` 镜像构建说明**即视为 S0 可关闭；**告警渠道选型**不作为 S0 阻塞项，须在 [reviews/phase-S0-review.md](./reviews/phase-S0-review.md) 登记遗留或已选方案 | 2026-04-28 |

详见 [github-repo.md](./github-repo.md)。

## S0 目标（工程壳）

- [x] 仓库内文档索引与阶段评审模板可用  
- [x] 最小 CI：不依赖内网 RAGFlow、不依赖生产 API Key（见基线第 8 / 13 节）  
- [x] Docker：`tbox-ragflow` 镜像构建路径与 `deploy/` 编排说明一致（可先仅 build profile；见根 `README.md`、`docs/docker-deploy.md`）  
- [x] 协作约定：`CONTRIBUTING`、PR 模板、分支命名 `stage/<N>-<name>`（见基线第 13 节）

## S1 目标（ingest skeleton）

- [x] `tbox-pipelines` 提供最小 CLI：`python -m tbox_pipelines.cli sync`  
- [x] 增加配置加载骨架：支持 `config/pipeline.sample.json` + 环境变量覆盖  
- [x] 增加数据源与入库链路占位：`ingest -> workflows -> ragflow client`  
- [x] 增加 Airflow DAG 占位：`airflow/dags/tbox_ingest_dag.py`（仅 scaffold 命令）  
- [x] 补充基础测试，保持 CI 绿（不依赖内网与生产密钥）

## S1 非目标

- 不对接真实 MCP 四服务与外网爬取站点（后续 S1.1）  
- 不绑定真实 RAGFlow 文档上传 API 细节（当前 endpoint 为占位）  
- 不实现角色权限业务逻辑

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-04-28 | 初稿：S0 范围占位 |
| 2026-04-28 | 补充：确认独立 GitHub 仓、`main`、S0 完成定义（含告警非阻塞） |
| 2026-04-28 | 切换到 S1：补充 ingest skeleton 目标与非目标 |
