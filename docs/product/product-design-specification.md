# 产品设计文档（Product Design Specification）

- 问题与目标：统一运维工具箱；账户以 sudo 登录为主；新旧机双轨且项目精简。
- 用户与场景：新机 simple 开户；旧机冻结不改目录组；约 3 年一次 DB 恢复。
- 范围：`apps/ansible`（simple + legacy 归档）、`apps/tools`、Makefile、`db-remind`。
- 非范围：强推旧机改属组、CI 连生产、Vault/AWX。
- 约束：本地域名；禁止提交 IP/口令/私钥/生产连接串。见 `docs/tech/account-policy.md`。
