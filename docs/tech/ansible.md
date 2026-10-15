# Ansible 用法

工程路径：`apps/ansible/`。

## 环境

Inventory 主机组：

- `dev_servers` — `TARGET_ENV=dev`
- `pro_servers` — `TARGET_ENV=pro`

Playbook 通过 `-e target_env=$TARGET_ENV` 选择组（默认 `dev`）。

## 常用 playbook

| Playbook | 作用 |
|----------|------|
| `playbooks/setup_users.yml` | 用户组 + 普通用户 + SSH/sudo |
| `playbooks/manage_groups.yml` | 仅用户组 |
| `playbooks/manage_users.yml` | 仅用户 |
| `playbooks/setup_root_users.yml` | root 权限用户 |
| `playbooks/cleanup_root_users.yml` | 清理 root 用户 / SSH 密钥 |
| `playbooks/python_upgrade.yml` | Python 升级辅助 |
| `playbooks/emergency_fix_permissions.yml` | 紧急权限修复 |

根目录 `make users` / `make root-users` / `make ping` 已封装上述常用操作。

## 变量

放在 `apps/ansible/vars/`。仓库只提交 `*.example` 与非敏感的 `system.yml`、`cleanup_users.yml`。

## 安全

- `ansible_host` 使用本地域名，不要写 IP。
- 不要提交 `inventory/hosts.yml`、`vars/users.yml`、`vars/root_users.yml`、`vars/groups.yml`、`vars/ssh_keys.yml`。
