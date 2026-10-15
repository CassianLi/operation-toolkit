# 生产库备份恢复（约每 3 年）

工程：`apps/tools/db-restore/`（原 `rds-bak-tools`）。

与 `apps/tools/db-history-cleanup/`（历史数据清理）不同：本 runbook 面向**整库备份恢复 / 手动部署**。

## 前置

1. 主机已安装 podman（或兼容的 compose 运行时）
2. `cp apps/tools/db-restore/env.example apps/tools/db-restore/.env`，本地填写口令（勿提交）
3. 按该目录 README 准备数据与备份目录（路径以 README 为准）
4. 将备份文件放到约定 backups 目录

## 执行摘要

```bash
cd apps/tools/db-restore
# 按 README 启动 compose / 查看日志 / 校验时区与连通性
```

详细步骤见：

- `apps/tools/db-restore/README.md`
- `apps/tools/db-restore/手动恢复数据指南.md`

## 完成后

1. 验证业务侧只读抽查（按你们当时 checklist）
2. 更新 `docs/tech/ops-calendar.md` 中 `db-restore` 的 `last_run` / `next_due`
3. 运行 `make db-remind` 确认已离开告警窗口

## 提醒

日常可用 `make db-remind`：距 `next_due` 不足 `warn_days` 天或已过期时会以非 0 退出。
