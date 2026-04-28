# RAGFlow overlay

此目录下的文件会在构建 `tbox-ragflow` 镜像时**复制到容器内 `/ragflow/`**。

## 用法

- 新增 TBOX 专用代码：例如 `overlay/custom/tbox/`（再在 Python 中注册路由或引用）。
- 覆盖上游文件：保持与 `upstream/ragflow` 相同的相对路径，例如 `overlay/api/apps/kb_app.py`（尽量少用，便于 merge）。

## 注意

仅改此处且 `FROM` 使用固定官方 tag 时，升级官方镜像请同步更新 `apps/ragflow-server/Dockerfile` 的 `BASE_IMAGE` 并做回归测试。
