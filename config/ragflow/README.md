# RAGFlow 配置说明

上游运行时配置由 `upstream/ragflow/docker/service_conf.yaml.template` 与 `upstream/ragflow/docker/.env` 生成。

若 TBOX 需要固定变更，可在此目录记录「与官方差异」或放置合并用的片段，并在 `docs/docker-deploy.md` 中写明如何挂载/注入。
