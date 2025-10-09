# Ansible Root权限用户管理工具

一个专门用于配置和管理具有root权限用户的Ansible工具，适用于需要root权限进行系统管理的场景。

## 🎯 核心功能

- **Root权限用户管理**: 创建具有root权限的用户账户
- **SSH密钥管理**: 自动配置SSH公钥认证
- **sudo权限配置**: 配置无密码sudo权限
- **安全配置**: 强化SSH安全设置
- **多环境支持**: 支持开发、测试、生产环境
- **审计日志**: 记录所有配置操作

## 📁 项目结构

```
ansible-asl-ser-root/
├── ansible.cfg                    # Ansible主配置文件
├── inventory/
│   └── hosts.yml                 # 服务器清单文件
├── global_vars/                  # 全局变量配置目录
│   ├── root_users.yml            # Root权限用户配置
│   ├── system.yml                # 系统配置变量
│   ├── ssh_keys.yml.example      # SSH密钥配置模板
│   └── ssh_keys.yml              # SSH密钥配置（敏感信息）
├── roles/
│   └── root_user_management/     # Root用户管理角色
│       ├── tasks/main.yml        # 主任务文件
│       ├── templates/sudoers.j2  # sudo配置模板
│       ├── handlers/main.yml     # 处理器文件
│       └── meta/main.yml         # 角色元数据
├── playbooks/
│   └── setup_root_users.yml      # 主配置playbook
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
# 或使用ED25519（推荐）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥到目标服务器
ssh-copy-id root@your-server-ip
```

### 3. 配置服务器信息

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
          server_description: "开发环境服务器"
          environment: "dev"
```

### 4. 配置Root权限用户

编辑 `global_vars/root_users.yml` 文件：

```yaml
root_users:
  - username: admin_user1
    full_name: "管理员用户1"
    shell: /bin/bash
    home: "/home/admin_user1"
    create_home: yes
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... admin1@example.com"
```

### 5. 配置SSH密钥（重要）

```bash
# 复制SSH密钥配置模板
cp global_vars/ssh_keys.yml.example global_vars/ssh_keys.yml

# 编辑SSH密钥配置，填入实际的SSH公钥
vim global_vars/ssh_keys.yml
```

### 6. 执行配置

```bash
# 执行Root权限用户配置
ansible-playbook playbooks/setup_root_users.yml

# 指定环境
ansible-playbook playbooks/setup_root_users.yml -e "target_env=dev"
ansible-playbook playbooks/setup_root_users.yml -e "target_env=pro"

# 指定服务器
ansible-playbook playbooks/setup_root_users.yml -e "target_env=dev" --limit "asl-dev-ser"
```

## 📋 配置说明

### Root权限用户配置

在 `global_vars/root_users.yml` 中配置用户信息：

#### 新用户配置（需要SSH密钥）
```yaml
root_users:
  - username: admin_user1
    full_name: "管理员用户1"
    shell: /bin/bash
    home: "/home/admin_user1"
    create_home: yes
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... admin1@example.com"
```

#### 已存在用户配置（保持现有SSH密钥）
```yaml
root_users:
  - username: existing_user
    full_name: "现有用户"
    shell: /bin/bash
    home: "/home/existing_user"
    create_home: no
    # 不配置 ssh_keys，保持现有SSH密钥配置
```

#### 已存在用户添加新SSH密钥
```yaml
root_users:
  - username: existing_user
    full_name: "现有用户"
    shell: /bin/bash
    home: "/home/existing_user"
    create_home: no
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... new_key@example.com"
```

### 权限配置

Root权限用户将获得以下权限：
- **sudo权限**: `ALL=(ALL) NOPASSWD:ALL` - 无密码执行所有root命令
- **用户组**: 每个用户将创建同名的用户组作为主组，确保权限隔离
- **SSH密钥认证**: 强制使用SSH密钥，禁用密码登录
- **安全配置**: 强化SSH安全设置

### 系统配置

在 `global_vars/system.yml` 中配置系统参数：

```yaml
system_info:
  os_family: "RedHat"
  os_version: "7"
  python_min_version: "3.8"

security:
  selinux:
    mode: "enforcing"
  firewall:
    default_zone: "public"
    services:
      - "ssh"
```

## 🛠️ 常用命令

### 标准使用流程

```bash
# 1. 检查连接
ansible all -m ping

# 2. 运行完整配置
ansible-playbook playbooks/setup_root_users.yml

# 3. 验证配置
ansible all -m shell -a "id admin_user1"
```

### 分步执行

```bash
# 只创建用户
ansible-playbook playbooks/setup_root_users.yml --tags users

# 只配置SSH密钥
ansible-playbook playbooks/setup_root_users.yml --tags ssh_keys

# 只配置sudo权限
ansible-playbook playbooks/setup_root_users.yml --tags sudo_config
```

### 其他命令

```bash
# 查看服务器列表
ansible all --list-hosts

# 测试连接
ansible all -m ping

# 检查用户配置
ansible all -m shell -a "id {{ item }}" --loop "{{ root_users | map(attribute='username') | list }}"

# 检查sudo权限
ansible all -m shell -a "sudo -l -U {{ item }}" --loop "{{ root_users | map(attribute='username') | list }}"
```

## 🔒 安全特性

### 核心安全措施

- **SSH密钥认证**: 强制使用SSH密钥，禁用密码登录
- **sudo无密码**: 配置sudo免密码执行，提高操作效率
- **最小权限原则**: 虽然给予root权限，但通过sudo实现
- **审计日志**: 记录所有配置操作和用户活动
- **敏感信息分离**: SSH密钥等敏感信息从版本控制中分离

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
   - `global_vars/root_users.yml` - Root权限用户基本信息配置
   - `global_vars/system.yml` - 系统配置变量

3. **安全建议**：
   - 定期轮换SSH密钥
   - 监控sudo操作日志
   - 定期审计用户活动
   - 备份配置文件

## 🔧 高级配置

### 多环境配置

支持开发、测试、生产环境：

```bash
# 开发环境
ansible-playbook playbooks/setup_root_users.yml -e "target_env=dev"

# 测试环境
ansible-playbook playbooks/setup_root_users.yml -e "target_env=test"

# 生产环境
ansible-playbook playbooks/setup_root_users.yml -e "target_env=pro"
```

### 自定义配置

#### 添加新用户

在 `global_vars/root_users.yml` 中添加：

```yaml
root_users:
  - username: new_admin
    full_name: "新管理员"
    shell: /bin/bash
    home: "/home/new_admin"
    create_home: yes
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... new_admin@example.com"
```

#### 修改系统配置

在 `global_vars/system.yml` 中修改：

```yaml
security:
  selinux:
    mode: "permissive"  # 修改SELinux模式
  firewall:
    services:
      - "ssh"
      - "http"  # 添加HTTP服务
```

### 故障排除

#### 常见问题

1. **SSH连接失败**：
   ```bash
   # 检查SSH服务状态
   ansible all -m service -a "name=sshd state=started"

   # 检查SSH配置
   ansible all -m shell -a "ss -tlnp | grep :22"
   ```

2. **sudo权限问题**：
   ```bash
   # 检查sudo配置
   ansible all -m shell -a "sudo -l -U admin_user1"

   # 验证sudoers文件语法
   ansible all -m shell -a "visudo -c"
   ```

3. **用户创建失败**：
   ```bash
   # 检查用户是否存在
   ansible all -m shell -a "id admin_user1"

   # 检查用户组
   ansible all -m shell -a "getent group admin_user1"
   ```

#### 调试方法

1. **使用verbose模式**：
   ```bash
   ansible-playbook playbooks/setup_root_users.yml -v
   ansible-playbook playbooks/setup_root_users.yml -vvv
   ```

2. **检查日志**：
   ```bash
   # 查看Ansible日志
   tail -f logs/ansible.log

   # 查看系统日志
   tail -f /var/log/secure
   ```

3. **验证配置**：
   ```bash
   # 检查inventory
   ansible-inventory --list

   # 检查变量
   ansible all -m debug -a "var=root_users"
   ```

## 📊 项目特点

### 简化设计
- **单一角色**: 只使用一个root_user_management角色
- **核心功能**: 专注于root权限用户管理
- **清晰结构**: 简单的目录结构，易于理解

### 易于扩展
- **模块化设计**: 角色和任务分离
- **模板化配置**: 使用Jinja2模板
- **变量化配置**: 所有配置都可以通过变量修改

### 安全可靠
- **SSH密钥认证**: 使用SSH密钥而非密码
- **sudo免密码**: 配置sudo免密码执行
- **审计日志**: 记录所有操作

## 🔍 与现有项目的关系

### 与 ansible-asl 项目的区别

| 特性     | ansible-asl                                  | ansible-asl-ser-root |
| -------- | -------------------------------------------- | -------------------- |
| 目标用户 | 普通用户（developers, operations, readonly） | Root权限用户         |
| 权限模型 | 基于用户组的细粒度权限                       | 完整的root权限       |
| 目录权限 | 复杂的目录权限配置                           | 不涉及目录权限       |
| 使用场景 | 日常开发和运维                               | 系统管理和紧急访问   |

### 协调使用

两个项目可以独立运行，也可以在同一台服务器上同时使用：

```bash
# 先配置普通用户
cd ../ansible-asl
ansible-playbook playbooks/setup_users.yml

# 再配置root权限用户
cd ../ansible-asl-ser-root
ansible-playbook playbooks/setup_root_users.yml
```

## 📞 支持

如有问题，请查看：
- 检查配置文件语法
- 查看日志文件
- 验证SSH连接和权限

## 📄 许可证

MIT License

---

**安全提醒**: 此工具配置的用户具有完整的root权限，请谨慎使用并确保：
1. SSH密钥安全存储
2. 定期审计用户操作
3. 监控系统日志
4. 定期轮换SSH密钥
