# 账户与目录权限策略（备忘）

## 现状（表述）

当前所有服务器均以 **sudo 账户** 登录，登录名因人/因机而异。部分已部署机器的共享目录曾挂过运维用户组（如 `developers`），便于当时非全量 sudo 场景下的协作。

**约束：**

1. **已部署服务器**：不做目录属组、ACL、用户组模型调整（有服务在跑）。
2. **新服务器**：一律采用 **simple** 规范——不建额外运维组；每人同名主组 + `NOPASSWD:ALL`；应用目录 `root:root` `0755`，写目录用 `sudo`。
3. 服务账户（nginx 等）由部署流程自行创建，与登录账户组无关。

## 工程对应

| | 新机（日常） | 旧机（冻结能力，偶发） |
|--|--------------|------------------------|
| 标记 | `account_profile: simple` | 默认 / `legacy` |
| 入口 | `make users-simple LIMIT=…` | `make users-legacy` 等 |
| 配置 | `vars/simple_users.yml`、`vars/system_simple.yml` | `vars/legacy/` |
| Playbook | `playbooks/setup_users_simple.yml` | `playbooks/legacy/` |

详见 [ansible.md](./ansible.md)。
