# 环境切换使用说明

## 概述

所有playbooks现在支持灵活选择目标环境，无需修改配置文件即可在开发环境和生产环境之间切换。

## 使用方法

### 1. 开发环境（默认）
```bash
# 使用默认开发环境
ansible-playbook playbooks/setup_users.yml
ansible-playbook playbooks/manage_users.yml
ansible-playbook playbooks/manage_groups.yml
ansible-playbook playbooks/python_upgrade.yml
```

### 2. 生产环境
```bash
# 指定生产环境
ansible-playbook playbooks/setup_users.yml -e "target_env=pro"
ansible-playbook playbooks/manage_users.yml -e "target_env=pro"
ansible-playbook playbooks/manage_groups.yml -e "target_env=pro"
ansible-playbook playbooks/python_upgrade.yml -e "target_env=pro"
```

### 3. 指定特定服务器
```bash
# 只对特定服务器执行
ansible-playbook playbooks/setup_users.yml -e "target_env=dev" --limit "asl-dev-gw"
ansible-playbook playbooks/setup_users.yml -e "target_env=pro" --limit "asl-pro-ser,asl-pro-gw"
```

## 环境配置

### 开发环境 (dev_servers)
- asl-dev-ser: ser.dev.asl.com
- asl-dev-gw: gw.dev.asl.com
- asl-dev-env: env.dev.asl.com

### 生产环境 (pro_servers)
- asl-pro-ser: ser.pro.asl.com
- asl-pro-gw: gw.pro.asl.com
- asl-pro-env: env.pro.asl.com
- asl-pro-basic: basic.pro.asl.com
- asl-pro-bg: bg.pro.asl.com
- asl-pro-mq: mq.pro.asl.com

## 常用命令示例

### 检查服务器状态
```bash
# 检查开发环境所有服务器
ansible dev_servers -m ping

# 检查生产环境所有服务器
ansible pro_servers -m ping

# 检查特定服务器
ansible asl-dev-gw -m ping
```

### 执行配置任务
```bash
# 在开发环境配置用户
ansible-playbook playbooks/setup_users.yml -e "target_env=dev"

# 在生产环境配置用户
ansible-playbook playbooks/setup_users.yml -e "target_env=pro"

# 只配置用户组
ansible-playbook playbooks/manage_groups.yml -e "target_env=dev"

# 只管理用户
ansible-playbook playbooks/manage_users.yml -e "target_env=pro"
```

### 升级Python
```bash
# 升级开发环境Python
ansible-playbook playbooks/python_upgrade.yml -e "target_env=dev"

# 升级生产环境Python
ansible-playbook playbooks/python_upgrade.yml -e "target_env=pro"
```

## 注意事项

1. **默认环境**: 如果不指定 `target_env`，默认使用开发环境
2. **安全性**: 生产环境操作前请确认配置正确
3. **测试**: 建议先在开发环境测试，确认无误后再在生产环境执行
4. **备份**: 生产环境操作前建议备份重要数据

## 故障排除

### 如果遇到Python版本问题
```bash
# 先升级Python
ansible-playbook playbooks/python_upgrade.yml -e "target_env=dev"

# 然后执行其他任务
ansible-playbook playbooks/setup_users.yml -e "target_env=dev"
```

### 如果遇到连接问题
```bash
# 检查SSH连接
ansible dev_servers -m ping
ansible pro_servers -m ping

# 检查特定服务器
ansible asl-dev-gw -m ping
```
