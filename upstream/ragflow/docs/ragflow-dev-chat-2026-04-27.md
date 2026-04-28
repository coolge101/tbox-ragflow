# RAGFlow 二次开发对话记录（首份样例）

> 记录日期：2026-04-27  
> 记录来源：本次与 Cursor 助手对话整理

---

## 1) 会话信息

- 日期：2026-04-27
- 参与人：项目维护者 + Cursor 助手
- 环境：
  - OS：Linux（当前工作机）
  - 分支：未指定
  - 提交哈希：未记录
  - 部署方式：Docker（重点）
- 本次目标（一句话）：明确 RAGFlow 启动方式、命令差异，并建立可共享对话记录机制

## 2) 背景与上下文

- 业务背景：准备基于 RAGFlow 做后续二次开发，需要先稳定启动和团队共享操作结论。
- 当前现状：仓库中已存在 Docker 启动配置和文档，用户给出了一套 Windows Git Bash 下的启动步骤。
- 已知限制：
  - 多终端/多设备需要共享对话结论
  - 需兼容不同命令习惯（`docker-compose` 与 `docker compose`）
- 相关目录/模块：
  - `docker/`
  - `README_zh.md`
  - `docker/README.md`
  - `docs/`

## 3) 对话关键结论（必填）

### 3.1 结论摘要

- [x] RAGFlow 推荐优先用 Docker 方式快速启动。
- [x] 用户给出的启动步骤与仓库文档推荐流程本质一致，主要差异在命令写法与 profile 显式声明。
- [x] 跨设备共享“对话内容”最稳妥方案是落地为仓库文档并通过 Git 同步。

### 3.2 为什么这样做（决策依据）

- 方案候选：
  - A：仅依赖 Cursor 历史会话同步
  - B：对话结论写入项目文档并 Git 同步
- 选择方案：B
- 选择理由：
  - 不依赖客户端会话历史能力，稳定可追溯
  - 支持团队协作和代码评审
  - 与项目版本演进强绑定
- 放弃理由（不选项）：
  - A 适合个人临时续聊，但不适合作为工程知识沉淀主通道

## 4) 可执行步骤（命令级）

> 本节记录本次确认过的启动命令。

### 4.1 启动/重启（Docker，一体部署）

```bash
cd /home/vboxuser/ragflow/docker
docker compose -f docker-compose.yml up -d
docker compose ps
```

可选检查（Linux 常见前置）：

```bash
sysctl vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
```

### 4.2 Windows Git Bash 路径示例（用户提供）

```bash
# 示例路径 1
cd "/c/Users/<Windows用户名>/ragflow-docker"

# 示例路径 2（共享目录）
cd "/d/AI-1/ragflow/ragflow-main/ragflow-main/docker"

docker-compose --profile cpu up -d
docker-compose ps
```

### 4.3 验证清单

- [x] 明确容器状态检查命令：`docker compose ps` / `docker-compose ps`
- [x] 明确日志检查命令：`docker logs -f docker-ragflow-cpu-1`
- [ ] 启动后浏览器访问并验证登录（待实际部署时执行）
- [ ] 配置默认 LLM API Key（待实际部署时执行）

## 5) 启动方式差异对比（本次重点）

- **命令入口差异**
  - 用户流程：`docker-compose --profile cpu up -d`
  - 本仓库建议：`docker compose -f docker-compose.yml up -d`

- **工具版本差异**
  - `docker-compose`：旧独立命令（v1 风格）
  - `docker compose`：Docker v2 推荐写法
  - 实际多数场景等价，优先建议 v2 写法

- **profile 指定方式差异**
  - 用户命令显式指定 `--profile cpu`
  - 仓库 `docker/.env` 默认包含：
    - `DEVICE=cpu`
    - `COMPOSE_PROFILES=${DOC_ENGINE},${DEVICE}`
  - 结论：在当前默认配置下，不显式写 `--profile cpu` 也会走 CPU 方案

- **健康检查深度差异**
  - `docker compose ps`：检查容器是否 `Up`
  - `docker logs -f ...`：检查应用是否真正初始化完成
  - 建议：两者结合使用

## 6) 代码/文档改动记录（本次）

### 6.1 新增文件

- `docs/ragflow-dev-chat-template.md`（对话记录模板）
- `docs/ragflow-dev-chat-2026-04-27.md`（本样例文件）

### 6.2 改动说明

- `docs/ragflow-dev-chat-template.md`：
  - 改了什么：新增可复用模板（会话信息、决策、命令、排障、回滚、TODO）
  - 为什么改：支持多设备、多人持续共享对话结论
  - 影响范围：仅文档，无运行时影响

- `docs/ragflow-dev-chat-2026-04-27.md`：
  - 改了什么：将本次对话关键信息结构化沉淀
  - 为什么改：提供“首份样例”，便于后续照着填
  - 影响范围：仅文档，无运行时影响

## 7) 风险与回滚

- 风险点：文档不及时更新导致“命令与实际环境脱节”。
- 影响面：后续开发人员可能按旧步骤操作。
- 回滚步骤：
  1. 回看最近变更记录，标记失效命令
  2. 按最新 `README_zh.md` / `docker/README.md` 对齐
  3. 提交文档修订

## 8) 待办与下一步

- [ ] 在目标机器上执行一次完整 Docker 启动并补充实际日志截图/关键输出
- [ ] 补充“默认端口与访问地址”在团队内网场景的约定
- [ ] 若进入二开，新增“改造目标与模块映射”章节（API、RAG、前端）

## 9) 附录

### 9.1 关键参考

- 启动主文档：`README_zh.md`
- Docker 变量与服务说明：`docker/README.md`
- 官方文档：[https://ragflow.io/docs/dev/](https://ragflow.io/docs/dev/)

### 9.2 跨设备共享建议（已确认）

- 把本文件纳入 Git 管理并及时提交
- 在另一台机器执行 `git pull` 后查看 `docs/` 下记录
- 需要续聊时，直接把“本文件链接 + 今日目标”发给助手
