# Design: operation-toolkit 脚手架与 Ansible/DB 运维整理

**日期:** 2026-10-15  
**状态:** 已批准并实施（分支 `chore/scaffold-reorg`）  
**范围:** 仓库脚手架规范化、Ansible 工程合并、DB 三年周期工具整理与防遗忘提醒

## 1. 背景与目标

当前仓库是长期积累的运维工具集：`operation/` 下两套近乎重复的 Ansible 工程、`tools/` 下 DB 备份恢复与历史清理脚本，根目录缺少统一 README/命令入口，文档过时且曾出现 IP 示例。目标是：

1. 按产品工作区脚手架统一目录：`docs/`、`tmp/`、`apps/`
2. 合并两套 Ansible 为单一工程，共享 inventory，用 playbook/role 区分普通用户与 root 用户
3. 整理 DB 相关工具（尤其三年一周期的备份恢复），并提供可执行的到期提醒
4. 全程不泄露服务器 IP、真实登录账户、密钥与生产连接串；主机一律本地域名

## 2. 决策摘要

| 议题 | 决策 |
|------|------|
| 整理深度 | 全面对齐脚手架，工程迁入 `apps/` |
| Ansible 组织 | 合并为 `apps/ansible/`（方案 A） |
| DB 工具 | 迁入 `apps/tools/`，纳入本轮范围 |
| 防遗忘 | 运维日历 + `make db-remind`（距到期 ≤ warn_days 或已过期则非 0 退出） |
| 环境划分 | 保留 inventory 主机组 `dev_servers` / `pro_servers`，不强制拆 `inventories/dev\|pro` |
| 非目标 | 不改 playbook 业务逻辑；不上 CI 连生产；不引入 Vault/AWX |

## 3. 顶层结构

```
operation-toolkit/
├── README.md
├── Makefile
├── .gitignore
├── docs/
│   ├── product/          # vision + PDS
│   ├── tech/             # ansible、db-restore、ops-calendar 等
│   ├── design/
│   ├── agent/            # Agent 硬约束
│   └── superpowers/      # 本设计与后续实施计划
├── tmp/                  # 本地缓存；真实内容不入库
│   ├── cases/ logs/ out/ store/
└── apps/
    ├── ansible/          # 唯一 Ansible 工程
    └── tools/
        ├── db-restore/           # 原 rds-bak-tools
        └── db-history-cleanup/   # 原 prod-db-history-cleanup
```

约定：

- 旧路径 `operation/`、`tools/` 迁移完成后删除；必要时短期保留 `MOVED.md` 指向新路径后再删
- 根目录散落过时文档（如对比类 md）迁入 `docs/tech/` 或删除重复内容
- 根 `.gitignore` **不再**忽略整个 `docs/`

## 4. Ansible（`apps/ansible/`）

```
apps/ansible/
├── ansible.cfg
├── inventory/
│   ├── hosts.yml.example    # 可入库：本地域名占位
│   └── hosts.yml            # 本地实配，gitignore
├── vars/
│   ├── users.yml.example / root_users.yml.example
│   ├── groups.yml.example / ssh_keys.yml.example
│   ├── system.yml
│   └── （对应实配文件本地生成，不入库）
├── roles/
│   ├── group_management/
│   ├── user_management/
│   ├── root_user_management/
│   └── root_user_cleanup/
├── playbooks/
│   ├── setup_users.yml
│   ├── manage_users.yml / manage_groups.yml
│   ├── setup_root_users.yml / cleanup_root_users.yml
│   ├── python_upgrade.yml
│   └── emergency_fix_permissions.yml
└── README.md                # 短说明；细节见 docs/tech/ansible.md
```

要点：

- 两套 inventory 合并为一份；`ansible_host` 仅本地域名；示例中的 `ansible_user` 用占位名
- 原 `global_vars/` 收拢到 `vars/`（或按需 `group_vars`），playbook 经 `vars_files` 显式加载
- 角色原样迁入，**本轮不改任务逻辑**
- 多份过时 README（QUICK_START、PROJECT_STRUCTURE 等）收敛为 `docs/tech/ansible.md` + 工程内短 README

## 5. DB 工具与防遗忘

### 5.1 目录

| 新路径 | 来源 | 用途 |
|--------|------|------|
| `apps/tools/db-restore/` | `tools/rds-bak-tools` | 生产库备份恢复（约每 3 年一次、手动部署） |
| `apps/tools/db-history-cleanup/` | `tools/prod-db-history-cleanup` | 历史数据清理（与三年恢复不同，文档需标明） |

### 5.2 运维日历

文件：`docs/tech/ops-calendar.md`

机器可解析的固定字段示例：

```markdown
## db-restore
- last_run: YYYY-MM-DD
- next_due: YYYY-MM-DD
- warn_days: 90
- runbook: ./db-restore.md
```

另附人工检查清单（备份位置、本机 `.env`、启动/校验步骤等），**不写真实密码与连接串**。

### 5.3 根 Makefile 入口

| 目标 | 作用 |
|------|------|
| `make help` | 列出全部入口 |
| `make ping ENV=dev\|pro` | Ansible 连通性 |
| `make users ENV=…` | 普通用户 playbook |
| `make root-users ENV=…` | root 用户 playbook |
| `make db-remind` | 读日历；到期窗口内或已过期则打印清单并以非 0 退出 |
| `make db-restore-docs` | 打印恢复 runbook 路径与检查清单 |

实现：`scripts/db-remind.sh`（或等价短 Python），无新依赖；输出可写入 `tmp/logs/`。

执行完一次三年恢复后，人工更新 `last_run` / `next_due`（可选后续加 `make db-mark-done DATE=…`，非本轮必须）。

## 6. 安全与忽略规则

硬约束（`docs/agent/` + 根 README）：

- 禁止提交或文档出现：原始 IP、真实登录口令、私钥内容、生产 DB 连接串
- Inventory / 示例一律本地域名；私钥仅引用本机路径（如 `~/.ssh/...`），不入库

根 `.gitignore` 关键项包括：

```
tmp/*
!tmp/**/.gitkeep
.env
.env.*
!.env.example
*.pem
*.key
**/inventory/hosts.yml
**/vars/users.yml
**/vars/root_users.yml
**/vars/ssh_keys.yml
**/vars/groups.yml
**/config/database.yaml
apps/tools/**/backups/
apps/tools/**/logs/
```

敏感实配一律配套 `*.example`。迁移时清理旧文档中的 IP 示例。

## 7. 迁移顺序

1. 搭脚手架：`docs/` 分层 stub、`tmp/`、根 README、`.gitignore`、`Makefile` 骨架  
2. 迁并 Ansible → `apps/ansible/`（角色/playbook 复制，合成 `hosts.yml.example`；本地 `hosts.yml` 不提交）  
3. 迁 tools → `apps/tools/...`；写 `docs/tech/db-restore.md`、`ops-calendar.md`；实现 `make db-remind`  
4. 移除旧 `operation/`、`tools/` 与过时根文档  
5. 自检：`make help`、`make db-remind`；有条件时 ansible check；文档敏感信息扫一眼  

## 8. 成功标准

- 新人打开根 README 能在 5 分钟内找到 Ansible 与 DB 恢复入口  
- 仅一套 Ansible inventory 需维护；两环境用组 + `ENV=` 区分  
- `make db-remind` 在到期窗口可失败告警，平时可安静通过  
- 仓库内无可识别的生产 IP / 明文密钥 / 生产 DB 口令  

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 合并 inventory 遗漏主机 | 以两套现有 hosts 的并集为准；迁移前后主机名清单对照 |
| 本地实配误提交 | 统一 gitignore + example；提交前检查 |
| 路径变更打断肌肉记忆 | 根 Makefile 作为唯一推荐入口；短期 MOVED 提示 |
| 日历未更新导致误报/漏报 | runbook 末步强制写回 `next_due`；remind 文案提示 |
