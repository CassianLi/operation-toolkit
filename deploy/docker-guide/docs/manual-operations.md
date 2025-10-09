# Docker Compose 手动操作指导

## 概述

本文档提供了Docker Compose部署时的手动操作指导，用于处理无法通过配置文件自动解决的问题。这些操作通常涉及系统级配置，需要管理员权限。

## 手动操作场景

### 1. 用户组不存在
当宿主机不存在目标用户组时，需要手动创建。

### 2. 权限配置复杂
当需要特殊的权限配置时，需要手动设置。

### 3. 系统限制
当系统有特殊限制时，需要手动调整。

### 4. 故障排除
当自动配置失败时，需要手动诊断和修复。

## 操作指导

### 1. 用户组管理

#### 创建用户组
```bash
# 创建developers用户组
sudo groupadd developers

# 创建指定GID的用户组
sudo groupadd -g 1002 developers

# 验证用户组创建
getent group developers
```

#### 添加用户到组
```bash
# 将当前用户添加到developers组
sudo usermod -aG developers $USER

# 将指定用户添加到组
sudo usermod -aG developers username

# 验证用户组成员
groups $USER
```

#### 删除用户组
```bash
# 删除用户组
sudo groupdel developers

# 注意：删除前确保没有用户依赖此组
```

### 2. 目录权限管理

#### 创建目录结构
```bash
# 创建主目录
sudo mkdir -p /opt/docker-apps

# 创建服务目录
sudo mkdir -p /opt/docker-apps/your-service/{data,logs,config,backups}

# 验证目录创建
tree /opt/docker-apps
```

#### 设置目录所有权
```bash
# 设置目录属于当前用户和developers组
sudo chown -R $USER:developers /opt/docker-apps

# 设置目录属于指定用户和组
sudo chown -R username:groupname /opt/docker-apps

# 验证目录所有权
ls -la /opt/docker-apps
```

#### 设置目录权限
```bash
# 设置目录权限为755
sudo chmod -R 755 /opt/docker-apps

# 设置目录权限为775（组可写）
sudo chmod -R 775 /opt/docker-apps

# 设置特定目录权限
sudo chmod 755 /opt/docker-apps
sudo chmod 775 /opt/docker-apps/your-service/data
sudo chmod 775 /opt/docker-apps/your-service/logs

# 验证目录权限
ls -la /opt/docker-apps
```

### 3. 用户ID映射

#### 获取用户信息
```bash
# 获取当前用户信息
id

# 获取指定用户信息
id username

# 获取用户组信息
getent group groupname

# 获取所有用户组
getent group
```

#### 创建用户映射
```bash
# 创建与容器用户ID相同的用户
sudo useradd -u 999 -g 999 -s /bin/false -d /nonexistent mysql

# 创建与容器组ID相同的组
sudo groupadd -g 999 mysql

# 验证用户创建
id mysql
```

### 4. SELinux配置（RHEL/CentOS）

#### 检查SELinux状态
```bash
# 检查SELinux状态
sestatus

# 检查SELinux模式
getenforce

# 查看SELinux上下文
ls -Z /opt/docker-apps
```

#### 配置SELinux
```bash
# 启用容器管理权限
sudo setsebool -P container_manage_cgroup on

# 设置目录SELinux标签
sudo chcon -Rt svirt_sandbox_file_t /opt/docker-apps

# 设置目录SELinux标签（更宽松）
sudo chcon -Rt container_file_t /opt/docker-apps

# 验证SELinux标签
ls -Z /opt/docker-apps
```

#### 临时禁用SELinux
```bash
# 临时禁用SELinux
sudo setenforce 0

# 永久禁用SELinux（需要重启）
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

# 重新启用SELinux
sudo setenforce 1
```

### 5. 防火墙配置

#### 检查防火墙状态
```bash
# 检查防火墙状态（Ubuntu/Debian）
sudo ufw status

# 检查防火墙状态（RHEL/CentOS）
sudo firewall-cmd --state

# 查看开放端口
sudo netstat -tlnp
```

#### 配置防火墙规则
```bash
# Ubuntu/Debian - 开放端口
sudo ufw allow 3306/tcp
sudo ufw allow 8080/tcp

# RHEL/CentOS - 开放端口
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# 验证防火墙规则
sudo ufw status numbered
sudo firewall-cmd --list-ports
```

### 6. 系统资源限制

#### 检查系统资源
```bash
# 检查内存使用
free -h

# 检查磁盘空间
df -h

# 检查CPU信息
lscpu

# 检查系统负载
uptime
```

#### 调整系统限制
```bash
# 检查文件描述符限制
ulimit -n

# 调整文件描述符限制
sudo vim /etc/security/limits.conf

# 添加以下内容：
# * soft nofile 65536
# * hard nofile 65536

# 重新加载限制
sudo systemctl daemon-reload
```

### 7. Docker配置

#### 检查Docker配置
```bash
# 检查Docker版本
docker --version
docker compose version

# 检查Docker服务状态
sudo systemctl status docker

# 检查Docker配置
docker info
```

#### 配置Docker
```bash
# 配置Docker用户组
sudo groupadd docker
sudo usermod -aG docker $USER

# 重新登录使组权限生效
newgrp docker

# 验证Docker权限
docker ps
```

### 8. 故障排除

#### 检查容器状态
```bash
# 查看容器状态
docker compose ps

# 查看容器日志
docker compose logs service-name

# 查看容器详细信息
docker inspect container-name
```

#### 检查权限问题
```bash
# 进入容器检查用户信息
docker compose exec service-name id

# 检查容器内目录权限
docker compose exec service-name ls -la /path/to/directory

# 检查挂载点
docker inspect container-name | grep -A 10 "Mounts"
```

#### 检查网络问题
```bash
# 检查网络连接
docker compose exec service-name ping hostname

# 检查端口监听
docker compose exec service-name netstat -tlnp

# 检查DNS解析
docker compose exec service-name nslookup hostname
```

## 常见问题解决

### 问题1: 权限拒绝错误
**错误**: `Permission denied`

**解决步骤**:
1. 检查目录权限: `ls -la /opt/docker-apps`
2. 检查用户组: `groups $USER`
3. 重新设置权限: `sudo chown -R $USER:developers /opt/docker-apps`
4. 重新设置权限: `sudo chmod -R 755 /opt/docker-apps`

### 问题2: 用户组不存在
**错误**: `group does not exist`

**解决步骤**:
1. 创建用户组: `sudo groupadd developers`
2. 添加用户到组: `sudo usermod -aG developers $USER`
3. 重新登录: `newgrp developers`

### 问题3: SELinux阻止访问
**错误**: `Operation not permitted`

**解决步骤**:
1. 检查SELinux状态: `sestatus`
2. 设置SELinux标签: `sudo chcon -Rt svirt_sandbox_file_t /opt/docker-apps`
3. 或临时禁用SELinux: `sudo setenforce 0`

### 问题4: 容器启动失败
**错误**: `container failed to start`

**解决步骤**:
1. 检查配置文件语法: `docker compose config`
2. 查看容器日志: `docker compose logs`
3. 检查资源限制: `docker stats`
4. 检查端口占用: `netstat -tlnp | grep port`

## 最佳实践

### 1. 操作前准备
- 备份重要数据
- 记录当前配置
- 准备回滚方案

### 2. 操作过程
- 逐步执行操作
- 验证每步结果
- 记录操作日志

### 3. 操作后验证
- 测试服务功能
- 检查系统状态
- 验证权限配置

### 4. 文档记录
- 记录操作步骤
- 记录配置变更
- 记录问题解决

## 注意事项

### 1. 安全考虑
- 使用最小权限原则
- 避免使用root用户
- 定期审查权限配置

### 2. 系统影响
- 评估操作对系统的影响
- 在维护窗口执行操作
- 准备应急方案

### 3. 数据保护
- 操作前备份数据
- 验证备份完整性
- 测试恢复流程

### 4. 监控告警
- 设置监控告警
- 关注系统日志
- 及时响应异常

## 相关文档

- [权限管理指南](docker-compose-permissions-guide.md)
- [通用配置模板](../examples/universal/README.md)
- [MySQL服务示例](../examples/mysql/README.md)
- [测试验证指南](testing-guide.md)
