# Patches

对 `upstream/ragflow` 内已有文件的修改，可导出为补丁放在此目录，便于 code review 与升级时重放。

## 生成补丁示例

在 `upstream/ragflow` 内完成修改并提交后：

```bash
cd upstream/ragflow
git format-patch -1 HEAD --stdout > ../../patches/0001-your-change.patch
```

## 应用

使用仓库根目录的 `scripts/apply-patches.sh`（会先 `git am` 或 `patch -p1`，按脚本说明操作）。
