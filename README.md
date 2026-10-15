# operation-toolkit

ASL 服务器运维工具箱：Ansible 账户管理 + 周期数据库备份恢复。

## 目录结构

| 路径 | 用途 |
|------|------|
| `docs/product/` | 愿景 / PDS |
| `docs/tech/` | Ansible、DB 恢复、运维日历 |
| `docs/agent/` | Agent 约束 |
| `tmp/` | 本地缓存（不入库真实内容） |
| `apps/ansible/` | 合并后的 Ansible 工程 |
| `apps/tools/db-restore/` | 约三年一次的备份恢复 |
| `apps/tools/db-history-cleanup/` | 生产库历史清理 |

## 常用命令

```bash
make help
make ping TARGET_ENV=dev
make users TARGET_ENV=dev
make root-users TARGET_ENV=pro
make db-remind
make db-restore-docs
```

首次使用 Ansible：复制 `apps/ansible/inventory/hosts.yml.example` → `hosts.yml`，以及所需 `vars/*.example` → 实配文件（均已 gitignore）。

## 安全

- Inventory 与敏感 vars 仅本地文件；仓库只保留 `*.example`。
- 文档与示例使用本地域名，不写 IP / 真实口令。
