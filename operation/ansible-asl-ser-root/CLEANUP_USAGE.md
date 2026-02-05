# Root权限用户清理功能使用指南

## 📋 功能概述

新增的清理功能支持两种模式：
1. **ssh_only模式**：仅清理SSH密钥，保留用户账户和其他配置
2. **full模式**：完全删除用户账户（用户、组、主目录、sudo配置、SSH密钥）

## 🚀 快速使用

### 1. 仅清理SSH密钥（推荐）

```bash
# 清理单个用户的SSH密钥
ansible-playbook playbooks/cleanup_root_users.yml \
  -e "target_env=dev" \
  -e "cleanup_mode=ssh_only" \
  -e "target_users=old_user"

# 清理多个用户的SSH密钥
ansible-playbook playbooks/cleanup_root_users.yml \
  -e "target_env=dev" \
  -e "cleanup_mode=ssh_only" \
  -e "target_users=user1,user2,user3"

# 指定服务器清理
ansible-playbook playbooks/cleanup_root_users.yml \
  -e "target_env=dev" \
  -e "cleanup_mode=ssh_only" \
  -e "target_users=old_user" \
  --limit "asl-dev-ser"
```

### 2. 完全删除用户账户

```bash
# 完全删除单个用户
ansible-playbook playbooks/cleanup_root_users.yml \
  -e "target_env=dev" \
  -e "cleanup_mode=full" \
  -e "target_users=temp_user"

# 完全删除多个用户
ansible-playbook playbooks/cleanup_root_users.yml \
  -e "target_env=dev" \
  -e "cleanup_mode=full" \
  -e "target_users=user1,user2,user3"
```

### 3. 使用配置文件

编辑 `global_vars/cleanup_users.yml`：

```yaml
cleanup_mode: "ssh_only"
target_users: "old_user1,old_user2"
```

然后运行：

```bash
ansible-playbook playbooks/cleanup_root_users.yml -e "target_env=dev"
```

## 🔧 配置选项

### 清理模式

- `ssh_only`：仅清理SSH密钥，保留用户账户和其他配置
- `full`：完全删除用户账户

### 目标用户

可以通过以下方式指定要清理的用户：

1. **命令行参数**：
   ```bash
   -e "target_users=user1,user2,user3"
   ```

2. **配置文件**：
   ```yaml
   target_users: "user1,user2,user3"
   ```

### 高级配置

在 `global_vars/cleanup_users.yml` 中可以配置：

```yaml
# 清理模式
cleanup_mode: "ssh_only"

# 目标用户
target_users: "user1,user2"

# 清理选项
cleanup_options:
  backup_user_data: false
  backup_directory: "/var/backups/ansible-root-users"
  force_cleanup: false
  send_notification: false
  notification_emails: []
  restart_services: false

# 安全配置
security:
  pre_cleanup_verification: true
  post_cleanup_verification: true
  detailed_logging: true
  audit_cleanup: true
```

## 📊 清理内容对比

| 清理项目   | ssh_only模式 | full模式 |
| ---------- | ------------ | -------- |
| SSH密钥    | ✅ 清理       | ✅ 清理   |
| SSH目录    | ✅ 删除       | ✅ 删除   |
| sudo配置   | ❌ 保留       | ✅ 删除   |
| 用户主目录 | ❌ 保留       | ✅ 删除   |
| 用户账户   | ❌ 保留       | ✅ 删除   |
| 用户组     | ❌ 保留       | ✅ 删除   |

## 🔍 验证清理结果

### 检查SSH密钥清理

```bash
# 检查SSH密钥文件是否存在
ansible all -m shell -a "ls -la /home/target_user/.ssh/"

# 检查authorized_keys文件
ansible all -m shell -a "cat /home/target_user/.ssh/authorized_keys"
```

### 检查用户账户状态

```bash
# 检查用户是否存在（full模式）
ansible all -m shell -a "id target_user"

# 检查用户组（full模式）
ansible all -m shell -a "getent group target_user"
```

### 检查sudo配置

```bash
# 检查sudo配置文件（full模式）
ansible all -m shell -a "ls -la /etc/sudoers.d/target_user"
```

## 📝 日志查看

### 清理执行日志

```bash
# 查看清理执行日志
tail -f /var/log/ansible-root-users/cleanup-execution.log

# 查看SSH密钥清理日志
tail -f /var/log/ansible-root-users/ssh-cleanup.log

# 查看用户删除日志（full模式）
tail -f /var/log/ansible-root-users/user-deletion.log
```

### Ansible执行日志

```bash
# 查看Ansible执行日志
tail -f logs/ansible.log
```

## ⚠️ 安全注意事项

### 清理前确认

1. **确认用户身份**：确保要清理的用户是正确的
2. **备份重要数据**：特别是使用full模式时
3. **检查依赖关系**：确认没有其他服务依赖该用户
4. **通知相关人员**：清理前通知相关用户

### 推荐做法

1. **优先使用ssh_only模式**：除非确实需要完全删除用户
2. **先在测试环境验证**：确保清理脚本正常工作
3. **逐步清理**：一次清理少量用户，避免批量操作风险
4. **保留审计日志**：所有清理操作都有详细日志记录

### 风险提示

1. **不可逆操作**：清理操作不可逆，请谨慎使用
2. **数据丢失风险**：full模式会删除用户主目录
3. **服务中断风险**：删除用户可能影响相关服务
4. **权限问题**：确保有足够的权限执行清理操作

## 🛠️ 故障排除

### 常见问题

1. **用户不存在**：
   ```bash
   # 检查用户是否存在
   ansible all -m shell -a "id target_user"
   ```

2. **权限不足**：
   ```bash
   # 检查当前用户权限
   ansible all -m shell -a "whoami"
   ansible all -m shell -a "sudo -l"
   ```

3. **清理失败**：
   ```bash
   # 查看详细错误信息
   ansible-playbook playbooks/cleanup_root_users.yml -vvv
   ```

### 调试方法

1. **使用verbose模式**：
   ```bash
   ansible-playbook playbooks/cleanup_root_users.yml -vvv
   ```

2. **检查日志**：
   ```bash
   tail -f /var/log/ansible-root-users/cleanup-execution.log
   ```

3. **验证配置**：
   ```bash
   ansible all -m debug -a "var=cleanup_mode"
   ansible all -m debug -a "var=target_user_list"
   ```

## 📞 支持

如有问题，请查看：
- 检查配置文件语法
- 查看日志文件
- 验证SSH连接和权限
- 确认目标用户存在性

---

**重要提醒**：清理操作不可逆，请在使用前充分测试并确认操作的正确性。
