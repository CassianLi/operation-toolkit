# MySQL 服务 Docker Compose 部署示例

## 概述

这是使用通用权限管理方案部署MySQL服务的完整示例。通过将MySQL容器内用户映射到宿主机用户组，解决权限问题，无需复杂的脚本配置。

## 核心特性

### 1. 权限管理
- 容器内用户映射到宿主机用户组
- 利用宿主机用户组的现有权限
- 避免复杂的用户创建和权限设置

### 2. 配置简化
- 优先使用Docker Compose配置文件
- 最小化脚本依赖
- 便于阅读和维护

### 3. 完整功能
- 包含PHPMyAdmin管理界面
- 健康检查和资源限制
- 完整的日志和备份配置

## 快速开始

### 步骤1: 获取宿主机用户信息
```bash
# 在宿主机运行以下命令
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 记录: HOST_USER_ID=1001, HOST_GROUP_ID=1002
```

### 步骤2: 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量文件
nano .env

# 设置必要的用户信息
HOST_USER_ID=1001
HOST_GROUP_ID=1002
HOST_USER_NAME=deployer
HOST_GROUP_NAME=developers

# 设置MySQL密码
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_user_password
```

### 步骤3: 创建目录结构
```bash
# 创建MySQL服务目录
mkdir -p {data,logs,config,backups,init-scripts}

# 设置目录权限
chown -R $USER:$(id -gn) .
chmod -R 755 .
```

### 步骤4: 启动服务
```bash
# 启动MySQL服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs mysql
```

### 步骤5: 验证部署
```bash
# 检查容器用户信息
docker compose exec mysql id

# 测试数据库连接
docker compose exec mysql mysql -u root -p -e "SHOW DATABASES;"

# 访问PHPMyAdmin
# 浏览器访问: http://localhost:8080
```

## 配置说明

### 关键配置项

#### 用户映射
```yaml
user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
```
这是核心配置，将MySQL容器内用户映射到宿主机用户组。

#### 卷挂载
```yaml
volumes:
  - ./data:/var/lib/mysql:rw      # 数据目录
  - ./logs:/var/log/mysql:rw      # 日志目录
  - ./config:/etc/mysql/conf.d:ro # 配置目录
  - ./backups:/backups:rw         # 备份目录
```

#### 环境变量
```yaml
environment:
  - USER_ID=${HOST_USER_ID}
  - GROUP_ID=${HOST_GROUP_ID}
  - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
  - MYSQL_DATABASE=${MYSQL_DATABASE}
```

### 目录结构
```
mysql/
├── docker-compose.yml    # Docker Compose配置
├── .env                  # 环境变量配置
├── data/                 # MySQL数据目录
├── logs/                 # MySQL日志目录
├── config/               # MySQL配置目录
│   └── my.cnf           # MySQL配置文件
├── backups/              # 备份目录
└── init-scripts/         # 初始化脚本目录
```

## 服务功能

### 1. MySQL数据库
- **端口**: 3306
- **用户**: root, app_user
- **数据库**: app_database
- **字符集**: utf8mb4

### 2. PHPMyAdmin管理界面
- **端口**: 8080
- **访问地址**: http://localhost:8080
- **用户名**: app_user
- **密码**: 与MYSQL_PASSWORD相同

### 3. 健康检查
- 自动检测MySQL服务状态
- 30秒间隔检查
- 3次重试机制

### 4. 资源限制
- 内存限制: 1GB
- CPU限制: 1.0核心
- 内存预留: 512MB
- CPU预留: 0.5核心

## 常见问题

### Q1: 如何获取宿主机用户信息？
```bash
# 运行id命令
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 对应配置: HOST_USER_ID=1001, HOST_GROUP_ID=1002
```

### Q2: MySQL容器启动失败怎么办？
1. 检查用户ID和组ID是否正确
2. 验证目录权限设置
3. 查看容器日志: `docker compose logs mysql`
4. 检查密码配置是否正确

### Q3: 如何验证权限配置？
```bash
# 进入容器检查用户信息
docker compose exec mysql id

# 检查数据目录权限
docker compose exec mysql ls -la /var/lib/mysql

# 检查日志目录权限
docker compose exec mysql ls -la /var/log/mysql
```

### Q4: 如何备份数据库？
```bash
# 创建备份
docker compose exec mysql mysqldump -u root -p --all-databases > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker compose exec -i mysql mysql -u root -p < backups/backup_20240101_120000.sql
```

## 维护操作

### 查看服务状态
```bash
# 查看容器状态
docker compose ps

# 查看资源使用
docker stats mysql-server

# 查看日志
docker compose logs -f mysql
```

### 重启服务
```bash
# 重启MySQL服务
docker compose restart mysql

# 重启所有服务
docker compose restart
```

### 停止服务
```bash
# 停止服务
docker compose down

# 停止并删除数据
docker compose down -v
```

## 安全建议

### 1. 密码安全
- 使用强密码
- 定期更换密码
- 不要在代码中硬编码密码

### 2. 网络安全
- 限制数据库访问IP
- 使用防火墙规则
- 考虑使用SSL连接

### 3. 数据安全
- 定期备份数据
- 测试备份恢复
- 监控磁盘空间

## 性能优化

### 1. 内存配置
```yaml
# 在docker-compose.yml中调整
deploy:
  resources:
    limits:
      memory: 2G  # 根据服务器内存调整
```

### 2. MySQL配置
```ini
# 在config/my.cnf中调整
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 500
```

### 3. 日志配置
```yaml
# 在docker-compose.yml中调整
logging:
  options:
    max-size: "200m"
    max-file: "5"
```

## 相关文档

- [通用权限管理指南](../docs/docker-compose-permissions-guide.md)
- [通用配置模板](../universal/README.md)
- [手动操作指导](../docs/manual-operations.md)
- [测试验证指南](../docs/testing-guide.md)
