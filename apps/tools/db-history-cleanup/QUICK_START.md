# 快速开始指南 (安全版本)

## 1. 环境准备

### 1.1 安装Python依赖
```bash
cd apps/tools/db-history-cleanup
pip3 install -r requirements.txt
```

### 1.2 创建必要目录
```bash
mkdir -p logs backups
```

### 1.3 验证安全版本
```bash
# 检查是否使用安全版本
python3 scripts/cleanup_manager.py --help
# 应该看到 "安全版本" 相关信息
```

## 2. 配置数据库连接

### 2.1 复制并编辑数据库配置
```bash
cp config/database.yaml.example config/database.yaml
vim config/database.yaml
```

### 2.2 配置示例
```yaml
database:
  host: "your-rds-endpoint.aliyuncs.com"
  port: 3306
  user: "cleanup_user"
  password: "your_secure_password"
  database: "your_database_name"
  charset: "utf8mb4"

  # 连接池配置
  pool:
    max_connections: 5
    min_connections: 1
    connection_timeout: 30
    read_timeout: 60

  # SSL配置（阿里云RDS推荐）
  ssl:
    enabled: true
    verify_cert: false
```

## 3. 配置清理规则

### 3.1 编辑清理规则
```bash
vim config/cleanup-rules.yaml
```

### 3.2 规则配置示例
```yaml
# 全局设置
global:
  retention_years: 5  # 保留5年
  batch_size: 1000    # 批处理大小
  max_execution_time: 3600  # 最大执行时间（秒）
  sleep_between_batches: 1  # 批处理间休眠时间（秒）
  dry_run: false      # 试运行模式

# 表配置
tables:
  - name: "user_logs"
    date_column: "created_at"
    retention_years: 5
    batch_size: 1000
    estimated_rows: 1000000
    enabled: true
    description: "用户操作日志表"

  - name: "system_events"
    date_column: "event_time"
    retention_years: 5
    batch_size: 500
    estimated_rows: 500000
    enabled: true
    description: "系统事件记录表"
```

## 4. 使用工具

### 4.1 数据分析
```bash
# 分析需要清理的数据量
./cleanup.sh analyze

# 生成详细分析报告
./cleanup.sh analyze --output logs/analysis_report.txt
```

### 4.2 试运行（推荐）
```bash
# 试运行，不实际删除数据（包含安全检查）
./cleanup.sh dry-run

# 试运行指定表
./cleanup.sh dry-run --table user_logs

# 查看安全检查结果
tail -f logs/cleanup.log | grep -E "(安全检查|主键|索引|警告)"
```

### 4.3 正式执行
```bash
# 执行实际清理（使用ID分页安全删除）
./cleanup.sh execute

# 执行指定表
./cleanup.sh execute --table user_logs
```

### 4.4 验证结果
```bash
# 验证清理结果
./cleanup.sh verify

# 验证指定表
./cleanup.sh verify --table user_logs
```

### 4.5 性能监控
```bash
# 获取性能影响分析
./cleanup.sh performance
```

## 5. 使用Python脚本

### 5.1 直接使用Python脚本
```bash
# 数据分析
python3 scripts/cleanup_manager.py --analyze

# 试运行
python3 scripts/cleanup_manager.py --dry-run

# 执行清理
python3 scripts/cleanup_manager.py --execute

# 验证结果
python3 scripts/cleanup_manager.py --verify
```

### 5.2 详细输出
```bash
python3 scripts/cleanup_manager.py --analyze --verbose
```

## 6. 日志查看

### 6.1 查看清理日志
```bash
# 查看最新日志
tail -f logs/cleanup.log

# 查看错误日志
grep ERROR logs/cleanup.log

# 查看清理统计
grep "CLEANUP_STATS" logs/cleanup.log
```

### 6.2 查看性能日志
```bash
tail -f logs/performance.log
```

## 7. 安全版本特性

### 7.1 新增安全功能
- **ID分页删除**：使用主键ID进行分页，避免重复删除或遗漏
- **表结构验证**：自动检查主键、索引、外键约束等
- **智能警告**：对潜在风险提供详细警告和建议
- **安全检查报告**：详细的执行统计和安全检查结果

### 7.2 安全检查清单
- [ ] 表有主键（必需）
- [ ] 日期字段有索引（推荐）
- [ ] 表大小合理
- [ ] 无外键约束影响
- [ ] 日期字段类型正确

## 8. 安全建议

### 8.1 执行前检查
- 确保数据库连接配置正确
- 验证清理规则配置
- 在测试环境先试运行
- 检查安全检查报告

### 8.2 执行时间
- 选择业务低峰期执行
- 避免在重要业务时段执行
- 预留足够的回滚时间

### 8.3 监控告警
- 设置数据库性能监控
- 配置清理进度告警
- 监控磁盘空间使用
- 关注安全检查报告

## 9. 故障排除

### 9.1 常见问题

**连接超时**
```bash
# 检查网络连接
ping your-rds-endpoint.aliyuncs.com

# 调整连接超时参数
# 在 config/database.yaml 中修改 connection_timeout
```

**权限错误**
```bash
# 确认用户权限
mysql -h your-rds-endpoint -u cleanup_user -p

# 检查表访问权限
SHOW GRANTS FOR 'cleanup_user'@'%';
```

**内存不足**
```bash
# 减少批处理大小
# 在 config/cleanup-rules.yaml 中修改 batch_size

# 增加休眠时间
# 在 config/cleanup-rules.yaml 中修改 sleep_between_batches
```

### 8.2 获取帮助
```bash
# 查看帮助信息
./cleanup.sh --help

# 查看Python脚本帮助
python3 scripts/cleanup_manager.py --help
```

## 9. 最佳实践

### 9.1 配置优化
- 根据数据量调整批处理大小
- 根据数据库性能调整休眠时间
- 设置合理的执行时间限制

### 9.2 监控指标
- 清理进度百分比
- 处理记录数
- 执行时间
- 数据库性能指标

### 9.3 定期维护
- 定期执行数据分析
- 监控清理效果
- 优化清理策略
