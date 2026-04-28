#!/usr/bin/env bash
# 将 patches/*.patch 应用到 upstream/ragflow（请按需修改 patch 级别与策略）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UP="$ROOT/upstream/ragflow"

cd "$UP"

shopt -s nullglob
patches=( "$ROOT"/patches/*.patch )
if [[ ${#patches[@]} -eq 0 ]]; then
  echo "patches/ 下没有 .patch 文件，跳过。"
  exit 0
fi

for p in "${patches[@]}"; do
  echo "Applying $p ..."
  patch -p1 < "$p"
done

echo "全部补丁已尝试应用；若有 reject 请手动处理。"
