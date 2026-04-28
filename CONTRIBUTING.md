# 贡献与协作约定（TBOX-RAGFlow）

权威基线见：`docs/TBOX-RAGFlow-知识库项目基线与Harness约定.md`。

## 分支

- 功能 / 阶段开发：`stage/<N>-<short-name>`  
- 集成主线：**`main`**（已确认；新建仓库请 `git branch -M main`）  
- 阶段结束：打 tag `v0.N.0` 或 `stage-N-done`（与基线第 13 节一致）

## GitHub 仓库

- 本工程使用 **独立远端仓** 管理本目录内容；说明见 `docs/github-repo.md`。

## PR 步长

- 一次 PR 只改**一个明确范围**（单模块、单目录或单一可审故事）  
- PR 正文必须使用模板（`.github/pull_request_template.md`）

## 密钥与配置

- **禁止**在源码与仓库 Markdown 中提交真实 API Key、Token、密码（基线第 8 节）  
- 仅使用占位符；运行时使用环境变量或挂载 `.env`（且 `.env` 不入库）

## 本地与 CI

- CI 默认使用 mock / `.env.example`，不依赖内网 RAGFlow  
- 本地可连接内网真实 RAGFlow 联调，与 CI 策略并存

## 文档

- 阶段文档固定于 `docs/` 根目录（基线第 12 节），见 `docs/README.md`
