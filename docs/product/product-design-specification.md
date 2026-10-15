# 产品设计文档（Product Design Specification）

- 问题与目标：旧仓库双 Ansible 工程 + 散落 tools，缺乏统一脚手架与管理命令。
- 用户与场景：配置普通/root 用户；按环境 ping/部署；每约 3 年一次生产库备份恢复。
- 范围：`apps/ansible`、`apps/tools`、根 Makefile、运维日历与 `db-remind`。
- 非范围：改 playbook 业务逻辑、CI 连生产、Ansible Vault/AWX。
- 约束：本地域名；禁止提交 IP/口令/私钥/生产连接串。
