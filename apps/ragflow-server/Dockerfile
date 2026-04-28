# TBOX: 在官方 RAGFlow 镜像上叠加自定义文件。
# 构建上下文必须为「平台根目录」：tbox-ragflow-platform/
#
#   docker build -f apps/ragflow-server/Dockerfile -t tbox-ragflow:local .
#
# 覆盖层目录 apps/ragflow-server/overlay/ 下的路径应与镜像内 /ragflow 下一致
#（例如 overlay/api/... → /ragflow/api/...）。

ARG BASE_IMAGE=infiniflow/ragflow:v0.24.0
FROM ${BASE_IMAGE}

COPY apps/ragflow-server/overlay/ /ragflow/
