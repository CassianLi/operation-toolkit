# Ansible 用法

工程：`apps/ansible/`。策略原文见 [account-policy.md](./account-policy.md)。

## 一句话

- **旧机**：sudo 登录已存在，目录组可能仍是历史配置 → **不调整**；偶发维护走 `playbooks/legacy/`。
- **新机**：`account_profile: simple` → 全员 sudo、无额外运维组、目录 `root:root`（写目录用 sudo）。

## 日常命令（新机优先）

```bash
make ping TARGET_ENV=pro LIMIT=<host>
make users-simple TARGET_ENV=pro LIMIT=<host>   # 必带 LIMIT
```

准备：

1. inventory 增加主机，`account_profile: simple`，本地域名  
2. `cp apps/ansible/vars/simple_users.yml.example apps/ansible/vars/simple_users.yml` 并填写  

## 旧机（legacy）

```bash
make users-legacy TARGET_ENV=pro LIMIT=<host>
make root-users-legacy TARGET_ENV=pro LIMIT=<host>
```

配置在 `apps/ansible/vars/legacy/`。**默认不要对旧机跑会改目录属组的任务。**

## 目录结构（精简后）

```
apps/ansible/
  playbooks/setup_users_simple.yml   # 主路径
  playbooks/python_upgrade.yml
  playbooks/legacy/                  # 旧机归档
  roles/root_user_management/        # simple 复用
  roles/simple_app_dirs/
  roles/legacy/                      # 旧机组/用户角色
  vars/simple_users.yml(.example)
  vars/system_simple.yml
  vars/legacy/                       # 旧机变量
```

## 安全

本地域名；勿提交实配 `hosts.yml` / `simple_users.yml` / `vars/legacy/*` 敏感文件。
