# 02 概要设计（架构与模块边界）

> **当前阶段**：S1 — ingest skeleton（最小可运行链路）  
> **权威基线**：[TBOX-RAGFlow-知识库项目基线与Harness约定.md](./TBOX-RAGFlow-知识库项目基线与Harness约定.md)

## 1. 逻辑架构（S1 scaffold）

```mermaid
flowchart LR
  subgraph users[用户]
    U[浏览器 / 内网用户]
  end
  subgraph ragflow[RAGFlow 基座]
    RF[RAGFlow 服务]
  end
  subgraph crawl[爬取与调度]
    MCP[MCP 四服务 TS/Node]
    AF[Apache Airflow]
    PG[(PostgreSQL 元数据)]
  end
  subgraph tbox[TBOX 扩展]
    CLI[tbox_pipelines.cli]
    SRC[ingest.sources]
    WF[workflows.sync_job]
    RC[ragflow.client]
  end

  U --> RF
  AF --> CLI
  CLI --> WF
  WF --> SRC
  WF --> RC
  RC --> RF
  MCP --> PG
  AF --> PG
```

## 2. 仓库与目录边界（与当前工程一致）

| 区域 | 职责 |
|------|------|
| `upstream/ragflow/` | RAGFlow 上游源码（fork / 同步） |
| `apps/ragflow-server/overlay/` | 对 RAGFlow 运行镜像的差量覆盖 |
| `packages/tbox-pipelines/` | 爬取入库、API 封装、批处理（与 Airflow DAG 衔接） |
| `packages/tbox-pipelines/airflow/dags/` | Airflow DAG 定义（S1 为 scaffold 占位） |
| `deploy/` | 对外 Docker Compose 与示例环境变量 |

## 3. S1 代码骨架清单

- CLI 入口：`packages/tbox-pipelines/src/tbox_pipelines/cli.py`  
- 配置：`packages/tbox-pipelines/src/tbox_pipelines/config.py`  
- 数据源占位：`packages/tbox-pipelines/src/tbox_pipelines/ingest/sources.py`  
- 入库占位：`packages/tbox-pipelines/src/tbox_pipelines/ragflow/client.py`  
- 编排：`packages/tbox-pipelines/src/tbox_pipelines/workflows/sync_job.py`  
- DAG 占位：`packages/tbox-pipelines/airflow/dags/tbox_ingest_dag.py`

## 4. 待 S1.1+ 补齐

- 接入真实 MCP 四服务的抓取任务与数据契约  
- 将 `ragflow.client` 占位 endpoint 替换为正式 API（并补集成测试）  
- 五类角色 × 能力矩阵（基线第 6 节、文档第 18 节）  
- 多数据集 ID 与配置策略（基线第 4.1 节）  
- 告警渠道具体实现（基线第 4.2 节）

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-04-28 | 初稿：S0 占位 |
| 2026-04-28 | 切换到 S1：补充 ingest skeleton 组件与链路 |
