# tbox-pipelines

TBOX 文档采集、清洗、调用 RAGFlow HTTP API / SDK 的批处理与工具代码。

## 本地开发

```bash
cd packages/tbox-pipelines
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Docker

见本目录 `Dockerfile`，由 `deploy/docker-compose.yml` 中 `tbox-worker` 服务引用（可选启用）。
