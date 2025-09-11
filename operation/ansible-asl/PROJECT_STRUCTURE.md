# 项目结构说明

本文档详细说明了Ansible用户管理工具的项目结构和各文件的作用。

## 📁 目录结构

```
ansible-dev/
├── ansible.cfg                    # Ansible主配置文件
├── inventory/
│   └── hosts.yml                 # 服务器清单文件
├── group_vars/
│   └── all.yml                   # 全局变量配置
├── roles/
│   └── user_management/          # 用户管理角色
│       ├── tasks/main.yml        # 主任务文件
│       ├── templates/sudoers.j2  # sudo配置模板
│       └── meta/main.yml         # 角色元数据
├── playbooks/
│   └── setup_users.yml           # 主配置playbook
├── logs/                         # 日志目录
├── README.md                     # 项目说明
├── QUICK_START.md                # 快速开始指南
└── PROJECT_STRUCTURE.md          # 项目结构说明
```

## 📋 文件说明

### 配置文件

#### `ansible.cfg`
Ansible的主配置文件，包含：
- **inventory**: 指定服务器清单文件路径
- **host_key_checking**: 禁用SSH主机密钥检查
- **timeout**: 设置连接超时时间
- **forks**: 设置并行执行的任务数
- **gathering**: 设置事实收集模式
- **roles_path**: 指定角色文件路径
- **log_path**: 指定日志文件路径

#### `inventory/hosts.yml`
服务器清单文件，定义：
- **服务器信息**: IP地址、用户名、SSH密钥路径
- **Python解释器**: 指定Python解释器路径
- **用户组配置**: 用户组名称、GID、描述
- **用户配置**: 用户名、全名、主组、次组、SSH密钥

#### `group_vars/all.yml`
全局变量配置文件，包含：
- **用户组权限**: 每个用户组的sudo命令列表
- **权限描述**: 用户组的名称和描述信息

### 角色文件


#### `roles/user_management/`
用户管理角色，包含所有用户相关的任务。

#### `roles/user_management/tasks/main.yml`
角色的主任务文件，执行以下操作：
1. **创建用户组**: 使用`group`模块创建用户组
2. **创建用户**: 使用`user`模块创建用户账户
3. **配置SSH**: 创建SSH目录、配置公钥、设置权限
4. **配置sudo**: 生成sudo配置文件

#### `roles/user_management/templates/sudoers.j2`
sudo配置模板文件，用于生成每个用户组的sudo配置文件。

#### `roles/user_management/meta/main.yml`
角色的元数据文件，包含：
- **角色信息**: 作者、描述、版本等
- **支持平台**: 支持的操作系统版本
- **依赖关系**: 角色依赖的其他角色

### Playbook文件

#### `playbooks/setup_users.yml`
主配置playbook，执行以下操作：
1. **环境检查**: 检查系统信息和安装必要软件包
2. **执行角色**: 调用user_management角色
3. **验证配置**: 验证用户组和用户创建结果

### 文档文件

#### `README.md`
项目的主要说明文档，包含：
- 项目概述和核心功能
- 项目结构说明
- 快速开始指南
- 配置说明和使用方法

#### `QUICK_START.md`
快速开始指南，帮助用户在5分钟内完成配置。

#### `PROJECT_STRUCTURE.md`
项目结构说明文档（本文件），详细说明各文件的作用。

## 🔧 配置层次说明

### 变量优先级
Ansible变量的优先级从高到低为：
1. **命令行变量** (`-e` 参数)
2. **playbook中的vars**
3. **roles/vars** (角色变量)
4. **group_vars** (组变量)
5. **roles/defaults** (角色默认值)

### 配置文件关系
```
ansible.cfg (主配置)
    ↓
inventory/hosts.yml (服务器清单)
    ↓
group_vars/all.yml (全局变量)
    ↓
roles/user_management/ (用户管理角色)
    ↓
playbooks/setup_users.yml (执行playbook)
```

## 🎯 核心概念

### 用户组配置
- **developers**: 开发人员组，拥有开发相关权限
- **readonly**: 只读用户组，只能查看系统信息

### 用户配置
- **主组**: readonly (所有用户的默认主组)
- **次组**: developers (开发人员的权限次组)

### 权限配置
- **sudo命令**: 每个用户组可以执行的sudo命令列表
- **SSH密钥**: 用户的SSH公钥配置
- **目录权限**: SSH目录的权限设置

## 🛠️ 自定义配置

### 添加新用户
在 `inventory/hosts.yml` 中的 `users` 部分添加：

```yaml
users:
  - username: newuser
    full_name: "新用户"
    primary_group: readonly
    secondary_groups: ["developers"]
    shell: /bin/bash
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... newuser@dev.com"
```

### 修改权限
在 `group_vars/all.yml` 中的 `group_permissions` 部分修改：

```yaml
group_permissions:
  developers:
    sudo_commands:
      - "/bin/systemctl status *"
      - "/bin/systemctl restart *"
      # 添加或删除命令...
```

### 添加新用户组
1. 在 `inventory/hosts.yml` 中添加用户组定义
2. 在 `group_vars/all.yml` 中添加权限配置
3. 重新运行playbook

## 📊 项目特点

### 简化设计
- **单一角色**: 只使用一个user_management角色
- **核心功能**: 专注于用户组和用户管理
- **清晰结构**: 简单的目录结构，易于理解

### 易于扩展
- **模块化设计**: 角色和任务分离
- **模板化配置**: 使用Jinja2模板
- **变量化配置**: 所有配置都可以通过变量修改

### 安全可靠
- **SSH密钥认证**: 使用SSH密钥而非密码
- **sudo免密码**: 配置sudo免密码执行
- **权限最小化**: 遵循最小权限原则

## 🔍 故障排除

### 常见问题
1. **配置文件语法错误**: 检查YAML语法
2. **SSH连接失败**: 检查SSH密钥和网络连接
3. **权限问题**: 检查sudo配置和用户权限

### 调试方法
1. **使用verbose模式**: `ansible-playbook -v playbooks/setup_users.yml`
2. **检查日志**: 查看 `logs/ansible.log` 文件
3. **验证配置**: 使用 `ansible-inventory --list` 检查inventory

## 📞 总结

这个项目结构设计简洁明了，专注于核心功能，易于理解和维护。通过合理的文件组织和配置层次，实现了用户组和用户管理的自动化。
