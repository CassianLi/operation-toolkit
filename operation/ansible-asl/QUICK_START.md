# 快速开始指南

本指南将帮助你在5分钟内快速设置和使用Ansible用户管理工具。

## 🚀 5分钟快速开始

### 步骤1: 安装Ansible (1分钟)

```bash
# macOS
brew install ansible

# CentOS7
sudo yum install -y epel-release ansible

# 验证安装
ansible --version
```

### 步骤2: 配置SSH密钥 (1分钟)

```bash
# 生成SSH密钥对
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 复制公钥到目标服务器
ssh-copy-id root@your-server-ip

# 测试SSH连接
ssh root@your-server-ip
```

### 步骤3: 配置服务器信息 (1分钟)

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

### 步骤4: 运行配置 (2分钟)

```bash
# 执行用户组和用户配置
ansible-playbook playbooks/setup_users.yml
```

## ✅ 验证配置

### 检查用户组
```bash
# 在目标服务器上执行
getent group developers
getent group readonly
```

### 检查用户
```bash
# 在目标服务器上执行
id dev001
id dev002
```

### 检查sudo权限
```bash
# 在目标服务器上执行
sudo -l -U dev001
sudo -l -U dev002
```

## 🎯 默认配置

### 用户组
- **developers**: 开发人员组 (GID: 1001)
- **readonly**: 只读用户组 (GID: 1002)

### 用户
- **dev001**: 开发人员001 (主组: readonly, 次组: developers)
- **dev002**: 开发人员002 (主组: readonly, 次组: developers)

### 权限
- **readonly**: 只能查看系统信息
- **developers**: 可以执行开发相关的系统命令

## 🔧 自定义配置

### 添加新用户
编辑 `inventory/hosts.yml` 文件中的 `users` 部分：

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
编辑 `group_vars/all.yml` 文件中的 `group_permissions` 部分：

```yaml
group_permissions:
  developers:
    sudo_commands:
      - "/bin/systemctl status *"
      - "/bin/systemctl restart *"
      # 添加更多命令...
```

## 🛠️ 常用命令

```bash
# 查看服务器列表
ansible all --list-hosts

# 测试连接
ansible all -m ping

# 运行配置
ansible-playbook playbooks/setup_users.yml

# 只创建用户组
ansible-playbook playbooks/setup_users.yml --tags groups

# 只创建用户
ansible-playbook playbooks/setup_users.yml --tags users

# 只配置SSH密钥
ansible-playbook playbooks/setup_users.yml --tags ssh_keys

# 只配置sudo权限
ansible-playbook playbooks/setup_users.yml --tags sudo
```

## 🔍 故障排除

### 常见问题

1. **SSH连接失败**
   ```bash
   # 检查SSH连接
   ssh -v root@your-server-ip
   ```

2. **Ansible连接失败**
   ```bash
   # 测试连接
   ansible all -m ping
   ```

3. **权限问题**
   ```bash
   # 检查sudo配置
   sudo visudo -c
   ```

### 获取帮助

- 📖 **项目结构**: 查看 `PROJECT_STRUCTURE.md`
- 📚 **详细说明**: 查看 `README.md`

## 🎉 完成！

恭喜！你已经成功配置了Ansible用户管理工具。现在可以：

- ✅ 自动管理用户组和用户
- ✅ 配置SSH密钥认证
- ✅ 设置sudo免密码权限
- ✅ 管理用户权限

## 📞 下一步

- 查看 `PROJECT_STRUCTURE.md` 了解项目结构
- 查看 `README.md` 了解详细功能
- 根据需要自定义配置
