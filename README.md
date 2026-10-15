# operation-toolkit

ASL 运维工具箱：Ansible 账户管理 + 周期数据库备份恢复。

## 账户策略（摘要）

所有服务器以 **sudo 账户** 登录（账户名因机而异）。部分旧机目录带历史用户组配置。  
**已部署机器不做调整**；**新机**采用精简规范（无额外运维组、全员 sudo、目录 `root:root`，写目录用 sudo）。

全文：[docs/tech/account-policy.md](docs/tech/account-policy.md)

## 目录

| 路径 | 用途 |
|------|------|
| `apps/ansible/` | Ansible（simple 主路径 + `legacy/` 归档） |
| `apps/tools/db-restore/` | 约三年一次备份恢复 |
| `apps/tools/db-history-cleanup/` | 历史数据清理 |
| `docs/tech/` | 技术说明与运维日历 |
| `tmp/` | 本地缓存（不入库） |

## 命令

```bash
make help
make users-simple TARGET_ENV=pro LIMIT=<新机主机名>
make db-remind
```
