# 安全配置指南

## 敏感信息管理

本项目将敏感信息（如SSH密钥）从版本控制中分离，以确保安全性。

### 文件结构

```
ansible-dev/
├── global_vars/
│   ├── ssh_keys.yml.example    # SSH密钥配置模板（可提交到版本控制）
│   ├── ssh_keys.yml           # SSH密钥配置文件（不应提交到版本控制）
│   ├── users.yml              # 用户配置变量
│   ├── groups.yml             # 用户组配置变量
│   └── system.yml             # 系统配置变量
├── .gitignore                 # Git忽略文件配置
└── SECURITY_GUIDE.md          # 本安全指南
```

### 配置步骤

#### 1. 创建SSH密钥配置文件

```bash
# 复制模板文件
cp global_vars/ssh_keys.yml.example global_vars/ssh_keys.yml

# 编辑配置文件，填入实际的SSH公钥
vim global_vars/ssh_keys.yml
```

#### 2. 配置SSH密钥

在 `global_vars/ssh_keys.yml` 文件中，将 `YOUR_SSH_PUBLIC_KEY_HERE` 替换为实际的SSH公钥：

```yaml
user_ssh_keys:
  duzhihui:
    - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... 1491700365@qq.com"
    - "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIc... 1491700365@qq.com"
```

#### 3. 验证配置

```bash
# 测试配置是否正确
ansible-playbook playbooks/manage_users.yml --check

# 实际执行用户管理
ansible-playbook playbooks/manage_users.yml
```

### 安全最佳实践

1. **永远不要提交敏感信息到版本控制**
   - `global_vars/ssh_keys.yml` 文件已添加到 `.gitignore`
   - 只提交 `global_vars/ssh_keys.yml.example` 模板文件

2. **文件权限管理**
   ```bash
   # 设置适当的文件权限
   chmod 600 global_vars/ssh_keys.yml
   ```

3. **定期轮换SSH密钥**
   - 定期更新SSH密钥
   - 及时移除不再使用的密钥

4. **环境隔离**
   - 不同环境使用不同的SSH密钥配置
   - 生产环境和开发环境分离

### 故障排除

#### 问题：SSH密钥配置不生效

**解决方案：**
1. 检查 `global_vars/ssh_keys.yml` 文件是否存在
2. 验证文件格式是否正确
3. 确认SSH公钥格式正确

#### 问题：用户无法SSH登录

**解决方案：**
1. 检查SSH密钥是否正确配置
2. 验证用户主目录权限
3. 检查SSH服务配置

### 文件说明

- `global_vars/ssh_keys.yml.example`: SSH密钥配置模板，包含示例格式
- `global_vars/ssh_keys.yml`: 实际的SSH密钥配置，包含敏感信息
- `global_vars/users.yml`: 用户基本信息配置
- `global_vars/groups.yml`: 用户组和权限配置
- `global_vars/system.yml`: 系统配置变量
- `.gitignore`: Git忽略文件，防止敏感信息被提交
- `SECURITY_GUIDE.md`: 本安全配置指南
