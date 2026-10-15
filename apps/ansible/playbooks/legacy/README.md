# Legacy playbooks（已上线机器）

**不要用于新机。** 新机用 `../setup_users_simple.yml`。

已部署服务器有服务在跑：此处 playbook **仅在确有需要时**对旧机 `--limit` 使用，且避免改动会动目录属组/ACL 的任务，除非你明确知道影响。

| Playbook | 说明 |
|----------|------|
| `setup_users.yml` | 旧：组 + 用户 + 组 sudo 白名单 |
| `manage_groups.yml` / `manage_users.yml` | 旧：分步 |
| `setup_root_users.yml` / `cleanup_root_users.yml` | 旧：root_users 清单 |
| `emergency_fix_permissions.yml` | 紧急修 /etc 等 |

变量在 `../../vars/legacy/`。策略说明见 `docs/tech/account-policy.md`。
