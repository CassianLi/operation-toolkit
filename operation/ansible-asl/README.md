# Ansible 用户管理工具

一个简化的Ansible工具，用于在CentOS7服务器上管理用户组、用户账户和SSH密钥。

## 🎯 核心功能

- **用户组管理**: 创建developers、operations和readonly三个用户组
- **用户管理**: 创建用户账户并分配到相应的用户组
- **SSH密钥管理**: 自动配置SSH公钥
- **权限配置**: 自动配置sudo免密码权限
- **Python版本检查**: 自动检查Python版本，如果<3.8则自动升级
- **权限更新**: 支持更新已存在用户组的权限配置
- **智能处理**: 自动处理已存在的用户组，避免GID冲突

## 📁 项目结构

```
ansible-dev/
├── ansible.cfg                    # Ansible主配置文件
├── inventory/
│   └── hosts.yml                 # 服务器清单文件
├── global_vars/                  # 全局变量配置目录
│   ├── users.yml                 # 用户配置变量
│   ├── groups.yml                # 用户组配置变量
│   ├── ssh_keys.yml.example      # SSH密钥配置模板
│   ├── ssh_keys.yml              # SSH密钥配置（敏感信息）
│   └── system.yml                # 系统配置变量
├── roles/
│   ├── group_management/         # 用户组管理角色
│   │   ├── tasks/main.yml        # 用户组管理任务
│   │   ├── templates/sudoers.j2  # sudo配置模板
│   │   └── meta/main.yml         # 角色元数据
│   └── user_management/          # 用户管理角色
│       ├── tasks/main.yml        # 用户管理任务
│       └── meta/main.yml         # 角色元数据
├── playbooks/
│   ├── setup_users.yml           # 主配置playbook
│   ├── manage_groups.yml         # 用户组管理playbook
│   ├── manage_users.yml          # 用户管理playbook
│   └── python_upgrade.yml        # Python升级playbook
├── logs/                         # 日志目录
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装Ansible
brew install ansible  # macOS
# 或
sudo yum install -y epel-release ansible  # CentOS7

# 验证安装
ansible --version
```

### 2. 配置SSH密钥

```bash
# 生成SSH密钥对
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 复制公钥到目标服务器
ssh-copy-id root@your-server-ip
```

### 3. 配置服务器信息

编辑 `inventory/hosts.yml` 文件：

### 4. 配置用户和权限

```bash
# 编辑用户配置
vim global_vars/users.yml

# 编辑用户组和权限配置
vim global_vars/groups.yml

# 编辑系统配置
vim global_vars/system.yml
```

### 5. 配置SSH密钥（重要）

```bash
# 复制SSH密钥配置模板
cp global_vars/ssh_keys.yml.example global_vars/ssh_keys.yml

# 编辑SSH密钥配置，填入实际的SSH公钥
vim global_vars/ssh_keys.yml
```

### 6. 执行配置

编辑 `inventory/hosts.yml` 文件：

```yaml
all:
  children:
    dev_servers:
      hosts:
        asl-dev-ser:
          ansible_host: 192.168.1.200  # 替换为你的服务器IP
          ansible_user: root
          ansible_ssh_private_key_file: ~/.ssh/id_rsa
          server_name: "asl-dev-ser"
```

### 4. 运行配置

```bash
# 执行用户组和用户配置
ansible-playbook playbooks/setup_users.yml
```

## 📋 用户组配置

### Developers（开发人员）
- **主组**: readonly
- **次组**: developers
- **权限**: 系统服务管理、进程管理、网络工具等
- **sudo命令**: 可以执行开发相关的系统命令

### Readonly（只读用户）
- **主组**: readonly
- **权限**: 只能查看系统信息
- **sudo命令**: 只能执行查看类命令

## 🔧 配置说明

### 用户配置
在 `inventory/hosts.yml` 中配置用户信息：

```yaml
users:
  - username: dev001
    full_name: "开发人员001"
    primary_group: readonly
    secondary_groups: ["developers"]
    shell: /bin/bash
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... dev001@dev.com"
```

### 权限配置
在 `group_vars/all.yml` 中配置用户组权限：

```yaml
group_permissions:
  developers:
    sudo_commands:
      - "/bin/systemctl status *"
      - "/bin/systemctl restart *"
      # 更多命令...
```

## 🛠️ 常用命令

### 标准使用流程

```bash
# 1. 检查Python版本
ansible-playbook check_python_version.yml

# 2. 如果Python版本不符合要求，先升级Python
ansible-playbook playbooks/python_upgrade.yml

# 3. 运行完整配置（推荐）
ansible-playbook playbooks/setup_users.yml
```

### 分步执行

```bash
# 只管理用户组和权限
ansible-playbook playbooks/manage_groups.yml

# 只管理用户和SSH密钥
ansible-playbook playbooks/manage_users.yml
```

### 其他命令

```bash
# 查看服务器列表
ansible all --list-hosts

# 测试连接
ansible all -m ping

# 使用标签执行特定任务
ansible-playbook playbooks/setup_users.yml --tags groups
ansible-playbook playbooks/setup_users.yml --tags users
ansible-playbook playbooks/setup_users.yml --tags ssh_keys
ansible-playbook playbooks/setup_users.yml --tags sudo

# 测试Python版本检查功能
ansible-playbook test_python_check.yml
```

## 🔒 安全特性

- SSH密钥认证
- sudo免密码配置
- 最小权限原则
- 权限审计功能
- **敏感信息分离**：SSH密钥等敏感信息已从版本控制中分离

### 安全配置说明

**重要**：本项目将SSH密钥等敏感信息从版本控制中分离，确保安全性：

1. **SSH密钥配置**：
   ```bash
   # 复制SSH密钥配置模板
   cp global_vars/ssh_keys.yml.example global_vars/ssh_keys.yml

   # 编辑SSH密钥配置，填入实际的SSH公钥
   vim global_vars/ssh_keys.yml
   ```

2. **文件说明**：
   - `global_vars/ssh_keys.yml.example` - SSH密钥配置模板（可提交到版本控制）
   - `global_vars/ssh_keys.yml` - SSH密钥配置文件（不应提交到版本控制）
   - `global_vars/users.yml` - 用户基本信息配置
   - `global_vars/groups.yml` - 用户组和权限配置
   - `global_vars/system.yml` - 系统配置变量
   - `.gitignore` - 已配置忽略敏感文件

3. **详细说明**：请参考 [SECURITY_GUIDE.md](SECURITY_GUIDE.md) 了解完整的安全配置指南。

## 📞 支持

如有问题，请查看：
- `PROJECT_STRUCTURE.md` - 项目结构说明
- `QUICK_START.md` - 快速开始指南

## 📄 许可证

MIT License
