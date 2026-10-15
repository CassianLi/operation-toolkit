# operation-toolkit

ASL 服务器运维工具箱：Ansible 账户管理 + 周期数据库备份恢复。

## 目录结构

| 路径 | 用途 |
|------|------|
| `docs/product/` | 愿景 / PDS |
| `docs/tech/` | Ansible、DB 恢复、运维日历 |
| `docs/agent/` | Agent 约束 |
| `tmp/` | 本地缓存（不入库真实内容） |
| `apps/ansible/` | Ansible 工程 |
| `apps/tools/` | DB 相关工具 |

## 常用命令

```bash
make help
```

完整命令表见 Makefile（Task 完成后以 `make help` 为准）。

## 安全

- Inventory 与敏感 vars 仅本地文件；仓库只保留 `*.example`。
- 文档与示例使用本地域名，不写 IP / 真实口令。
