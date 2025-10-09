# 快速开始指南

本指南将帮助您在5分钟内完成Root权限用户的配置。

## 🚀 5分钟快速配置

### 步骤1: 环境检查 (1分钟)

```bash
# 检查Ansible是否已安装
ansible --version

# 如果未安装，请先安装Ansible
# macOS:
brew install ansible

# CentOS/RHEL:
sudo yum install -y epel-release ansible

# Ubuntu/Debian:
sudo apt update && sudo apt install -y ansible
```

### 步骤2: 配置服务器信息 (1分钟)

编辑 `inventory/hosts.yml` 文件，修改服务器IP地址：

```yaml
all:
  children:
    dev_servers:
      hosts:
        asl-dev-ser:
          ansible_host: 192.168.1.200  # 修改为你的服务器IP
          ansible_user: root
          ansible_ssh_private_key_file: ~/.ssh/id_rsa
          server_name: "asl-dev-ser"
          server_description: "开发环境服务器"
          environment: "dev"
```

### 步骤3: 配置用户信息 (1分钟)

编辑 `global_vars/root_users.yml` 文件，修改用户信息：

```yaml
root_users:
  - username: your_admin_user  # 修改为你的用户名
    full_name: "你的姓名"
    shell: /bin/bash
    home: "/home/your_admin_user"
    create_home: yes
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... your_email@example.com"  # 修改为你的SSH公钥
```

### 步骤4: 配置SSH密钥 (1分钟)

```bash
# 复制SSH密钥配置模板
cp global_vars/ssh_keys.yml.example global_vars/ssh_keys.yml

# 编辑SSH密钥配置
vim global_vars/ssh_keys.yml
```

在 `ssh_keys.yml` 文件中填入你的SSH公钥：

```yaml
root_user_ssh_keys:
  your_admin_user:
    keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... your_email@example.com"
    description: "你的SSH公钥"
```

### 步骤5: 执行配置 (1分钟)

```bash
# 测试连接
ansible all -m ping

# 执行配置
ansible-playbook playbooks/setup_root_users.yml

# 验证配置
ansible all -m shell -a "id your_admin_user"
```

## ✅ 配置完成

如果一切正常，你将看到类似以下的输出：

```
TASK [显示配置完成信息] ****************************************
ok: [asl-dev-ser] => {
    "msg": "========================================\nRoot权限用户配置完成！\n========================================\n服务器: asl-dev-ser (192.168.1.200)\n环境: dev\n配置时间: 2024-01-01T12:00:00Z\n\n配置用户:\n- your_admin_user (你的姓名)\n\n安全提醒:\n1. 请确保SSH密钥安全存储\n2. 定期审计用户操作日志\n3. 建议定期轮换SSH密钥\n4. 监控sudo操作日志: /var/log/secure\n5. 配置文件备份位置: /etc/sudoers.d/\n\n验证命令:\n- 检查用户: id your_admin_user\n- 检查sudo权限: sudo -l -U your_admin_user\n- 检查SSH密钥: ls -la /home/your_admin_user/.ssh/\n========================================"
}
```

## 🔍 验证配置

### 检查用户创建

```bash
# 在目标服务器上执行
id your_admin_user
# 输出应该显示用户已创建

# 检查用户主目录
ls -la /home/your_admin_user/
```

### 检查sudo权限

```bash
# 在目标服务器上执行
sudo -l -U your_admin_user
# 输出应该显示: (ALL) NOPASSWD: ALL
```

### 检查SSH密钥

```bash
# 在目标服务器上执行
ls -la /home/your_admin_user/.ssh/
# 应该看到 authorized_keys 文件

# 检查SSH密钥内容
cat /home/your_admin_user/.ssh/authorized_keys
```

### 测试SSH登录

```bash
# 从本地测试SSH登录
ssh your_admin_user@your-server-ip

# 测试sudo权限
sudo whoami
# 应该输出: root
```

## 🚨 常见问题

### 问题1: SSH连接失败

**错误信息**: `Permission denied (publickey)`

**解决方案**:
1. 检查SSH密钥是否正确配置
2. 确保SSH公钥已添加到 `global_vars/ssh_keys.yml`
3. 检查SSH服务是否运行: `systemctl status sshd`

### 问题2: 用户创建失败

**错误信息**: `useradd: user 'username' already exists`

**解决方案**:
1. 用户已存在，这是正常的
2. 如果需要重新创建，先删除用户: `userdel -r username`

### 问题3: sudo权限配置失败

**错误信息**: `visudo: /etc/sudoers.d/username: syntax error`

**解决方案**:
1. 检查sudo配置文件语法: `visudo -c -f /etc/sudoers.d/username`
2. 如果语法错误，删除文件重新运行playbook

### 问题4: Python版本不符合要求

**错误信息**: `Python版本不符合要求！`

**解决方案**:
1. 安装Python3: `yum install -y python3`
2. 或者升级Python到3.8以上版本

## 📞 获取帮助

如果遇到问题，请：

1. 检查日志文件: `tail -f logs/ansible.log`
2. 使用verbose模式运行: `ansible-playbook playbooks/setup_root_users.yml -vvv`
3. 查看系统日志: `tail -f /var/log/secure`

## 🔒 安全提醒

配置完成后，请确保：

1. **SSH密钥安全**: 私钥文件权限设置为600
2. **定期审计**: 监控 `/var/log/secure` 中的sudo操作
3. **密钥轮换**: 定期更换SSH密钥
4. **访问控制**: 限制root权限用户的数量

---

**恭喜！** 您已成功配置了Root权限用户。现在可以使用配置的用户进行系统管理操作了。
