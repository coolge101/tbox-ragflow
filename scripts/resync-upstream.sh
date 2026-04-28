#!/usr/bin/env bash
# 将「本仓库的父目录」中的 ragflow 同步到 upstream/ragflow（排除平台自身与可再生目录）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# 默认：平台与 RAGFlow 同放在「父目录」下时，父目录即为 RAGFlow 根。
# 独立克隆时请显式指定：export RAGFLOW_SRC=/path/to/ragflow
SRC="${RAGFLOW_SRC:-$(cd "$ROOT/.." && pwd)}"
DEST="$ROOT/upstream/ragflow"

echo "SRC=$SRC"
echo "DEST=$DEST"

if [[ ! -d "$SRC/api" || ! -f "$SRC/Dockerfile" ]]; then
  echo "错误：SRC 不像 RAGFlow 仓库根目录（缺少 api/ 或 Dockerfile）。" >&2
  exit 1
fi

mkdir -p "$DEST"

rsync -a --delete \
  --no-owner --no-group \
  --exclude='tbox-ragflow-platform' \
  --exclude='.venv' \
  --exclude='web/node_modules' \
  --exclude='docker/ragflow-logs' \
  --exclude='**/__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='htmlcov' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.eggs' \
  --exclude='*.egg-info' \
  "$SRC/" "$DEST/"

echo "同步完成。"
