.PHONY: sync build-tbox-ragflow help

help:
	@echo "Targets:"
	@echo "  sync              - rsync 父目录 ragflow 到 upstream/ragflow（见 scripts/resync-upstream.sh）"
	@echo "  build-tbox-ragflow - docker build 生成 tbox-ragflow:local"

sync:
	@./scripts/resync-upstream.sh

build-tbox-ragflow:
	docker build -f apps/ragflow-server/Dockerfile -t tbox-ragflow:local .
