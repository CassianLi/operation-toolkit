# 生产数据库历史数据清理工具 (ID版本)

## 概述
本工具用于安全地清理生产MySQL数据库中的历史数据，支持阿里云RDS环境。**最新版本使用基于ID字段的清理策略**，避免日期字段无默认值的问题，确保清理过程安全、高效且对数据库压力最小。

## 特性
- 🔒 **安全优先**：基于ID字段清理、ID分页删除、表结构验证、完整的备份验证、事务控制、错误回滚
- ⚡ **高效执行**：分批处理、智能休眠、进度跟踪、主键索引优化
- 📊 **详细监控**：实时日志、性能监控、清理统计、安全检查报告
- 🛠️ **灵活配置**：YAML配置、多表支持、自定义规则
- 🔄 **可回滚**：完整的回滚机制和备份策略
- 🛡️ **智能验证**：自动检查主键、索引、外键约束等表结构
- 🔍 **ID查询工具**：提供ID分布查询和配置建议功能

## 文件结构
```
prod-db-history-cleanup/
├── config/
│   ├── database.yaml          # 数据库连接配置
│   ├── cleanup-rules.yaml     # 清理规则配置
│   └── logging.yaml           # 日志配置
├── scripts/
│   ├── cleanup_manager.py     # 主清理管理脚本
│   ├── db_connector.py        # 数据库连接管理
│   ├── data_analyzer.py       # 数据分析工具
│   ├── backup_manager.py      # 备份管理工具
│   ├── safe_cleanup_executor.py # 安全清理执行器 (推荐)
│   ├── cleanup_executor.py    # 原始清理执行器 (已弃用)
│   └── id_query_tool.py       # ID查询工具
├── logs/                      # 日志目录
├── backups/                   # 备份目录
├── requirements.txt           # Python依赖
├── cleanup.sh                 # 执行脚本
└── README.md                  # 本文件
```

## 快速开始

### 1. 环境准备
```bash
cd tools/prod-db-history-cleanup

# 安装Python依赖
pip3 install -r requirements.txt

# 创建必要目录
mkdir -p logs backups
```

### 2. 配置数据库连接
```bash
# 复制并编辑数据库配置
cp config/database.yaml.example config/database.yaml
vim config/database.yaml
```

### 3. 配置清理规则
```bash
# 编辑清理规则
vim config/cleanup-rules.yaml
```

### 4. 执行清理
```bash
# 试运行（不实际删除数据）
./cleanup.sh --dry-run

# 正式执行
./cleanup.sh --execute
```

## 配置说明

### 数据库配置 (database.yaml)
```yaml
database:
  host: "your-rds-endpoint.aliyuncs.com"
  port: 3306
  user: "cleanup_user"
  password: "secure_password"
  database: "your_database"

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

### 清理规则配置 (cleanup-rules.yaml)
```yaml
# 全局设置
global:
  batch_size: 1000
  max_execution_time: 3600  # 秒
  sleep_between_batches: 1  # 秒
  dry_run: false

# 表配置列表
# 使用ID字段进行清理，max_id为手动查询并配置的ID最大值
# 由于有的表日期字段没有设置非空和默认值，造成部分数据无法按日期切割，因此转为使用自增ID进行数据切割
# 将清理表中ID小于此max_id的所有数据
tables:
  - name: "user_logs"
    max_id: 1000000  # 手动查询并配置的ID最大值
    batch_size: 1000
    estimated_rows: 1000000
    enabled: true
    description: "用户日志表"

  - name: "system_events"
    max_id: 500000  # 手动查询并配置的ID最大值
    batch_size: 500
    estimated_rows: 500000
    enabled: true
    description: "系统事件表"
```

## 使用方法

### 1. 数据分析
```bash
# 分析需要清理的数据量
python3 scripts/cleanup_manager.py --analyze
```

### 2. 试运行
```bash
# 试运行，不实际删除数据
python3 scripts/cleanup_manager.py --dry-run --verbose
```

### 3. 正式执行
```bash
# 执行清理
python3 scripts/cleanup_manager.py --execute --verbose
```

### 4. 验证结果
```bash
# 验证清理结果
python3 scripts/cleanup_manager.py --verify
```

### 5. ID查询工具
```bash
# 查询所有表的ID分布信息
python3 scripts/id_query_tool.py

# 查询指定表的ID信息
python3 scripts/id_query_tool.py --table user_logs

# 生成ID信息报告
python3 scripts/id_query_tool.py --report id_report.txt

# 生成配置建议
python3 scripts/id_query_tool.py --config-suggestion config_suggestion.yaml
```

## 安全特性

### 1. 基于ID字段的清理策略
- **避免日期字段问题**：使用ID字段清理，避免日期字段无默认值的问题
- **避免重复删除**：使用主键ID分页，确保每条记录只删除一次
- **避免遗漏删除**：通过ID范围精确控制删除范围
- **性能优化**：主键索引查询，比日期字段排序更快
- **一致性保证**：使用 `IN` 子句精确删除指定ID的记录

### 2. 表结构智能验证
- **主键检查**：自动检测表是否有主键，无主键的表拒绝自动清理
- **索引检查**：检查ID字段是否有索引，提供性能优化建议
- **外键约束检查**：提醒可能存在的外键影响
- **字段类型验证**：验证ID字段的数据类型和可空性
- **表大小评估**：大表提供执行时间警告
- **ID配置验证**：检查配置的max_id是否合理

### 3. 数据保护
- 清理前自动创建表级备份
- 事务控制确保原子性
- 完整的错误处理和回滚机制

### 4. 执行安全
- 分批处理避免长时间锁表
- 智能休眠减少数据库压力
- 实时监控和告警
- 安全检查统计和报告

### 5. 访问控制
- 专用清理用户，最小权限原则
- SSL连接加密
- 连接池管理

### 6. ID查询工具特性
- **ID分布分析**：查询表的ID范围、总记录数、平均ID等统计信息
- **配置建议**：基于数据分布自动生成max_id配置建议
- **清理预览**：计算使用建议配置时的清理记录数和比例
- **报告生成**：生成详细的ID信息报告和配置建议文件
- **单表查询**：支持查询指定表的ID信息

## 监控和日志

### 日志级别
- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 监控指标
- 清理进度百分比
- 处理记录数
- 执行时间
- 数据库性能指标
- 错误统计

## 故障排除

### 常见问题

1. **连接超时**
   - 检查网络连接
   - 调整连接超时参数
   - 验证RDS白名单设置

2. **权限错误**
   - 确认用户权限
   - 检查表访问权限
   - 验证SSL配置

3. **内存不足**
   - 减少批处理大小
   - 增加休眠时间
   - 调整连接池大小

### 日志查看
```bash
# 查看最新日志
tail -f logs/cleanup.log

# 查看错误日志
grep ERROR logs/cleanup.log

# 查看清理统计
grep "CLEANUP_STATS" logs/cleanup.log
```

## 最佳实践

### 1. 执行时间
- 选择业务低峰期执行
- 避免在重要业务时段执行
- 预留足够的回滚时间

### 2. 监控告警
- 设置数据库性能监控
- 配置清理进度告警
- 监控磁盘空间使用

### 3. 备份策略
- 清理前确保有完整备份
- 保留清理前的表级备份
- 定期验证备份完整性

## 版本信息
- 版本: 2.0.0 (安全版本)
- 支持MySQL版本: 5.7+
- 支持环境: 阿里云RDS
- 最后更新: 2024年
- 主要更新: 升级为ID分页安全删除策略
