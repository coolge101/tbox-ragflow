# Docker 部署说明（TBOX 平台）

## 镜像分工

| 镜像 | 说明 |
|------|------|
| `tbox-ragflow:local` | 官方 RAGFlow 基础镜像 + `apps/ragflow-server/overlay/` |
| `tbox-worker:local` | `packages/tbox-pipelines` 批处理（可选） |

## 构建

在平台根目录：

```bash
docker build -f apps/ragflow-server/Dockerfile -t tbox-ragflow:local .
docker compose -f deploy/docker-compose.yml --profile tbox-image-build build tbox-ragflow
```

## 与官方全栈组合

生产环境建议以 `upstream/ragflow/docker/docker-compose.yml` 为基准，将其中 `ragflow`（或等价服务）的 `image` 替换为 `tbox-ragflow:local`，并统一 `env_file`、卷与网络命名；具体合并方式随你们运维规范而定（可复制一份到 `deploy/` 再改）。
