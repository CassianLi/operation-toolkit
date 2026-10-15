# 运维日历

机器可读字段供 `make db-remind` / `scripts/db-remind.sh` 解析。完成一次周期操作后请更新 `last_run` 与 `next_due`。

## db-restore

- last_run: 2025-07-23
- next_due: 2028-07-23
- warn_days: 90
- runbook: ./db-restore.md

### 检查清单（人工）

- [ ] 确认备份介质与校验
- [ ] 本机准备 `apps/tools/db-restore/.env`（由 `env.example` 复制，勿提交）
- [ ] 按 runbook 启动并验证
- [ ] 更新本文件的 `last_run` / `next_due`（通常 +3 年）
