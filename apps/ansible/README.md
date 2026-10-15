# Ansible（ASL）

**现状：** 各机均以 sudo 账户登录（账户名各异）；部分旧机目录曾设运维组。  
**原则：** 已部署机器不调整；新机只用 simple。详见 [account-policy.md](../../docs/tech/account-policy.md)。

## 新机（主路径）

```bash
# inventory: account_profile: simple
cp vars/simple_users.yml.example vars/simple_users.yml
make users-simple TARGET_ENV=pro LIMIT=<主机名>
```

目录：`system_simple.yml` → `root:root`；写部署目录请 **sudo**。

## 旧机（归档）

```bash
make users-legacy TARGET_ENV=pro LIMIT=<主机名>   # 确有必要时
```

配置与 playbook：`vars/legacy/`、`playbooks/legacy/`。避免改旧机目录属组。
