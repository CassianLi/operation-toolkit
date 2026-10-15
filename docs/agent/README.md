# Agent 文档

- 产品：ASL 运维工具箱（Ansible 用户管理 + 周期 DB 恢复）。
- 目录：`docs/` 文档、`tmp/` 本地缓存、`apps/` 可运行工程。
- 硬约束：禁止在提交或回复中泄露服务器 IP、真实登录账户/口令、私钥、生产 DB 连接串；主机使用本地域名。
- 入口：根目录 `make help`。
- 账户：全机 sudo 登录；旧机不调整目录组；新机 `account_profile: simple` + `make users-simple LIMIT=…`。详见 `docs/tech/account-policy.md`。legacy 仅在 `playbooks/legacy/`、`vars/legacy/`。
