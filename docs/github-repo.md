# GitHub 仓库约定（独立仓）

**已确认**：本工程以 **`tbox-ragflow-platform` 作为独立 Git 远端仓库** 管理（与「整仓 fork RAGFlow 且平台为子目录」相对）。

## 仓库根目录应包含

- `upstream/ragflow/`：RAGFlow 源码副本（同步策略见 [upstream-sync.md](./upstream-sync.md)）
- `apps/`、`packages/`、`deploy/`、`docs/`、`.github/` 等

## 初始化远端（示例）

在平台根目录执行：

```bash
cd /path/to/tbox-ragflow-platform
git init
git branch -M main
git remote add origin git@github.com:<org>/tbox-ragflow-platform.git
```

### 本机已执行（模板仓）

已在目录 **`tbox-ragflow-platform`** 根完成：

- `git init -b main`
- 删除 **`upstream/ragflow/.git`**，避免嵌套仓库，便于单仓推送
- 首条提交：`chore: initial commit for TBOX RAGFlow platform (S0)`

你只需在 GitHub 上**新建空仓库**（不要勾选「自动添加 README」），然后：

```bash
cd /home/vboxuser/ragflow/tbox-ragflow-platform
git remote add origin git@github.com:<org>/<repo>.git   # 若已存在 origin 则改为 set-url
git push -u origin main
```

或使用 GitHub CLI（已登录时）：

```bash
cd /home/vboxuser/ragflow/tbox-ragflow-platform
gh repo create <org>/tbox-ragflow-platform --private --source=. --remote=origin --push
```

首次推送前请将 **`upstream/ragflow`** 的体积与是否纳入 LFS 纳入团队策略（大仓可选 `git submodule` 替代全量拷贝）。

### 独立仓初始化与「内层 `.git`」

若 `upstream/ragflow` 由 **整仓拷贝/rsync** 得到，目录内可能带有 **嵌套的 `.git`**。在本平台根目录执行 `git init` 作为**唯一远端仓**时，应**删除** `upstream/ragflow/.git`，否则父仓库 `git add` 时会出现子模块/嵌套仓库异常。删除后仍可用 `scripts/resync-upstream.sh` 从本机 RAGFlow 根目录同步文件；长期更推荐改为 **git submodule** 指向官方仓库固定 tag。

## CI

工作流位于本仓 `.github/workflows/`；默认仅构建 **`packages/tbox-pipelines`**，不依赖内网与真实密钥。
