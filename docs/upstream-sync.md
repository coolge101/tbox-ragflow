# 与上游 RAGFlow 同步

- **源码真相**：`upstream/ragflow`（保留 `git remote` 指向官方，便于 `fetch` / `merge`）。
- **你的差量**：优先 `apps/ragflow-server/overlay/` 与 `patches/`。
- **禁止**：在 `upstream/ragflow` 内大量无记录修改；若必须改，请提交到独立分支并文档化。

## 建议流程

1. `cd upstream/ragflow && git fetch origin && git merge origin/main`（分支名按实际）
2. 解决冲突后运行测试与 Docker 构建
3. 平台根执行 `./scripts/resync-upstream.sh` 仅在「从旁路仓库覆盖拷贝」时使用；日常以 git 为主
