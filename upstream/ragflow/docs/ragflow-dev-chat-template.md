# RAGFlow 二次开发对话记录模板

> 用途：在多台机器、多人协作时，持续沉淀“和 Cursor/助手的有效对话结论”。
> 建议：每次讨论后只补充关键结论，避免粘贴整段冗长聊天。

---

## 1) 会话信息

- 日期：
- 参与人：
- 环境：
  - OS：
  - 分支：
  - 提交哈希（`git rev-parse --short HEAD`）：
  - 部署方式：`docker` / `source`
- 本次目标（一句话）：

## 2) 背景与上下文

- 业务背景：
- 当前现状：
- 已知限制（性能、资源、权限、时间窗口）：
- 相关目录/模块：
  - `api/`
  - `rag/`
  - `deepdoc/`
  - `web/`
  - `docker/`

## 3) 对话关键结论（必填）

### 3.1 结论摘要

- [ ] 结论 1：
- [ ] 结论 2：
- [ ] 结论 3：

### 3.2 为什么这样做（决策依据）

- 方案候选：
  - A：
  - B：
- 选择方案：
- 选择理由：
- 放弃理由（不选项）：

## 4) 可执行步骤（命令级）

> 只保留验证通过的命令；失败命令放到“问题排查”。

### 4.1 启动/重启

```bash
# 示例：Docker 启动
cd /path/to/ragflow/docker
docker compose -f docker-compose.yml up -d
docker compose ps
```

### 4.2 开发模式

```bash
# 示例：依赖服务
docker compose -f docker/docker-compose-base.yml up -d

# 示例：后端
source .venv/bin/activate
export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh

# 示例：前端
cd web && npm run dev
```

### 4.3 验证清单

- [ ] 容器状态 `Up`
- [ ] 后端日志无致命错误
- [ ] 前端可访问
- [ ] 能成功创建/导入知识库
- [ ] 能成功发起一次对话并返回结果

## 5) 代码改动记录

### 5.1 改动文件

- `path/to/file1`
- `path/to/file2`

### 5.2 改动说明（按文件）

- `path/to/file1`：
  - 改了什么：
  - 为什么改：
  - 影响范围：

- `path/to/file2`：
  - 改了什么：
  - 为什么改：
  - 影响范围：

### 5.3 配置变更

- `docker/.env`：
- `docker/service_conf.yaml.template`：
- 其他：

## 6) 问题排查与修复

### 6.1 问题现象

- 现象：
- 触发条件：
- 日志关键字：

### 6.2 排查过程

1. 操作：
2. 结果：
3. 结论：

### 6.3 最终修复

- 修复动作：
- 是否需要重启：
- 回归验证结果：

## 7) 风险与回滚

- 风险点：
- 影响面：
- 回滚步骤：
  1. 
  2. 
  3. 

## 8) 待办与下一步

- [ ] TODO 1（负责人 / 截止时间）
- [ ] TODO 2（负责人 / 截止时间）
- [ ] TODO 3（负责人 / 截止时间）

## 9) 附录（可选）

### 9.1 常用命令速查

```bash
# 查看容器
docker compose ps

# 查看 ragflow 日志
docker logs -f docker-ragflow-cpu-1

# 停止容器
docker compose down
```

### 9.2 参考链接

- 项目 README：`README_zh.md`
- Docker 说明：`docker/README.md`
- 官方文档：https://ragflow.io/docs/dev/

---

## 使用建议（简版）

- 每次对话后更新“3) 对话关键结论 + 8) 待办与下一步”。
- 每次代码改动后更新“5) 代码改动记录”。
- 每次故障排查后更新“6) 问题排查与修复”。
- 跨设备同步方式：提交该文件到 Git 仓库并在另一台机器 `git pull`。
