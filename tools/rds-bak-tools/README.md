# MySQL 5.7 数据库服务配置

## 概述
本项目提供了基于podman-compose的MySQL 5.7数据库服务配置，支持从备份文件自动或手动恢复数据。

## 文件结构
```
db-tools/
├── mysql-bak-db.yaml          # podman-compose主配置文件
├── mysql.cnf                  # MySQL配置文件
├── env.example                # 环境变量示例文件
├── init-scripts/
│   └── 01-restore-backup.sh   # 自动恢复脚本
├── check-timezone.sh          # 时区验证脚本
├── 手动恢复数据指南.md         # 手动恢复详细指南
└── README.md                  # 本文件
```

## 快速开始

### 1. 环境准备
确保已安装podman和podman-compose：
```bash
# 安装podman
sudo dnf install podman

# 安装podman-compose
pip3 install podman-compose
```

### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp env.example .env

# 编辑.env文件，设置安全的密码
vim .env
```

### 3. 创建必要目录
```bash
# 创建数据目录
sudo mkdir -p /data/databases/mysql/data
sudo mkdir -p /data/databases/mysql/backups

# 设置权限
sudo chown -R 999:999 /data/databases/mysql/
```

### 4. 放置备份文件
将备份文件 `mysql57_sysafari_20250723.qp` 放置到：
```
/data/databases/mysql/backups/mysql57_sysafari_20250723.qp
```

### 5. 启动服务
```bash
# 启动MySQL服务
podman-compose up -d

# 查看服务状态
podman-compose ps

# 查看日志
podman-compose logs mysql57
```

## 配置说明

### 主要特性
- **MySQL 5.7**：稳定可靠的数据库版本
- **数据持久化**：数据存储在 `/data/databases/mysql/data`
- **备份恢复**：支持从.qp格式备份文件恢复
- **安全配置**：包含多项安全优化设置
- **性能优化**：针对生产环境优化的配置参数
- **健康检查**：自动监控数据库服务状态
- **资源限制**：防止资源过度使用
- **时区同步**：自动使用宿主机时区设置

### 安全配置
- 禁用 `local_infile`
- 启用 `skip_name_resolve`
- 设置 `no-new-privileges`
- 使用临时文件系统
- 限制网络访问

### 性能配置
- InnoDB缓冲池：1GB
- 最大连接数：200
- 查询缓存：64MB
- 字符集：utf8mb4

### 时区配置
- 自动使用宿主机时区设置
- 支持宿主机的网络时间同步
- 无需手动配置时区参数

## 数据恢复

### 自动恢复
服务启动时会自动检查备份文件并尝试恢复。如果备份文件存在且格式正确，会自动执行恢复操作。

### 手动恢复
如果自动恢复失败或需要更精确的控制，请参考 `手动恢复数据指南.md` 文件。

## 常用操作

### 连接数据库
```bash
# 使用root用户连接
podman-compose exec mysql57 mysql -u root -p

# 使用应用用户连接
podman-compose exec mysql57 mysql -u sysafari_user -p sysafari
```

### 查看服务状态
```bash
# 查看容器状态
podman-compose ps

# 查看实时日志
podman-compose logs -f mysql57

# 查看健康检查状态
podman-compose exec mysql57 mysqladmin ping -u root -p

# 验证时区设置
./check-timezone.sh
```

### 备份数据库
```bash
# 创建数据库备份
podman-compose exec mysql57 mysqldump -u root -p --all-databases > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份特定数据库
podman-compose exec mysql57 mysqldump -u root -p sysafari > sysafari_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 停止和重启
```bash
# 停止服务
podman-compose down

# 重启服务
podman-compose restart

# 重新构建并启动
podman-compose up -d --build
```

## 故障排除

### 常见问题

1. **权限错误**
   ```bash
   sudo chown -R 999:999 /data/databases/mysql/
   ```

2. **端口冲突**
   - 检查3306端口是否被占用
   - 修改 `mysql-bak-db.yaml` 中的端口映射

3. **内存不足**
   - 增加容器内存限制
   - 调整MySQL配置参数

4. **备份文件格式不支持**
   - 参考手动恢复指南中的格式转换方法

### 日志查看
```bash
# 查看MySQL错误日志
podman-compose exec mysql57 tail -f /var/log/mysql/error.log

# 查看慢查询日志
podman-compose exec mysql57 tail -f /var/log/mysql/slow.log
```

## 监控和维护

### 定期维护任务
1. **日志轮转**：定期清理日志文件
2. **备份验证**：测试备份文件的可用性
3. **性能监控**：监控数据库性能指标
4. **安全更新**：定期更新MySQL版本

### 性能监控
```bash
# 查看连接数
podman-compose exec mysql57 mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# 查看慢查询
podman-compose exec mysql57 mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query_log%';"

# 查看InnoDB状态
podman-compose exec mysql57 mysql -u root -p -e "SHOW ENGINE INNODB STATUS\G"
```

## 安全建议

1. **强密码**：使用复杂的密码
2. **网络隔离**：限制数据库访问IP
3. **定期备份**：建立自动备份策略
4. **访问控制**：限制用户权限
5. **监控告警**：设置异常访问告警

## 技术支持

如遇到问题，请：
1. 查看日志文件
2. 参考故障排除部分
3. 检查配置文件语法
4. 验证环境变量设置

## 版本信息
- MySQL版本：5.7
- 配置文件版本：1.0
- 最后更新：2024年



https://eu-central-1-internal.bak.rds.aliyuncs.com/custins400005951/hins100576458_data_20250719195106_qp.xb?Expires=1753345227&OSSAccessKeyId=STS.NXwcNAQPgbXLR1MzxgScYUCrw&Signature=HqZdBtVzGjRPxTiMlsvCjAE0a4I%3D&Region=eu-central-1&Incb=1
