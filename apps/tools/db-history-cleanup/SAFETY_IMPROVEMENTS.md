# 数据库清理工具安全改进建议

基于Context7提供的数据库安全和DevSecOps最佳实践，以下是对`safe_cleanup_executor.py`的安全改进建议：

## 🔒 关键安全问题

### 1. SQL注入防护不足
**当前问题：**
- 使用字符串格式化构建SQL查询，存在SQL注入风险
- 表名和字段名直接拼接到SQL中

**改进建议：**
```python
# 当前代码（不安全）
select_sql = f"""
    SELECT {primary_key}
    FROM {table_name}
    WHERE {where_clause}
    ORDER BY {primary_key}
    LIMIT %s
"""

# 改进方案（安全）
def _validate_identifier(self, identifier: str) -> bool:
    """验证标识符是否安全"""
    import re
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))

def _safe_delete_batch_by_id(self, ...):
    # 验证表名和字段名
    if not self._validate_identifier(table_name) or not self._validate_identifier(primary_key):
        raise ValueError("Invalid table or column name")

    # 使用参数化查询
    select_sql = """
        SELECT {}
        FROM {}
        WHERE {}
        ORDER BY {}
        LIMIT %s
    """.format(primary_key, table_name, where_clause, primary_key)
```

### 2. 事务管理不完善
**当前问题：**
- 缺乏明确的事务边界
- 没有回滚机制

**改进建议：**
```python
def _perform_safe_cleanup(self, ...):
    """执行安全清理"""
    try:
        # 开始事务
        with self.db_connector.transaction():
            # 执行清理操作
            records_cleaned = 0
            last_id = None
            batch_count = 0

            while records_cleaned < total_records:
                # 批量删除操作
                batch_records, last_id = self._safe_delete_batch_by_id(...)
                records_cleaned += batch_records

                # 每10个批次提交一次
                if batch_count % 10 == 0:
                    self.db_connector.commit()

    except Exception as e:
        # 自动回滚
        self.db_connector.rollback()
        raise
```

### 3. 权限验证缺失
**当前问题：**
- 没有验证数据库用户权限
- 缺乏操作权限检查

**改进建议：**
```python
def _check_user_permissions(self, table_name: str) -> bool:
    """检查用户是否有删除权限"""
    try:
        # 检查DELETE权限
        sql = """
            SELECT COUNT(*) as has_delete
            FROM information_schema.table_privileges
            WHERE table_schema = %s
            AND table_name = %s
            AND privilege_type = 'DELETE'
            AND grantee = CURRENT_USER()
        """
        result = self.db_connector.execute_query(
            sql, (self.db_connector.config["database"]["database"], table_name)
        )
        return result[0]["has_delete"] > 0
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return False

def _cleanup_table_safely(self, table_config: Dict[str, Any], dry_run: bool):
    # 添加权限检查
    if not self._check_user_permissions(table_name):
        raise PermissionError(f"用户没有表 {table_name} 的删除权限")
```

### 4. 资源限制不足
**当前问题：**
- 缺乏内存使用限制
- 没有连接池管理
- 缺少执行时间限制

**改进建议：**
```python
class SafeCleanupExecutor:
    def __init__(self, db_connector: DatabaseConnector, config_file: str):
        # 添加资源限制配置
        self.resource_limits = {
            "max_memory_mb": 1024,  # 最大内存使用
            "max_execution_time": 3600,  # 最大执行时间
            "max_batch_size": 5000,  # 最大批次大小
            "connection_timeout": 30,  # 连接超时
        }

    def _check_resource_usage(self) -> bool:
        """检查资源使用情况"""
        import psutil
        import time

        # 检查内存使用
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        if memory_usage > self.resource_limits["max_memory_mb"]:
            logger.warning(f"内存使用超过限制: {memory_usage:.2f}MB")
            return False

        # 检查执行时间
        if self.execution_stats["start_time"]:
            elapsed_time = (datetime.now() - self.execution_stats["start_time"]).total_seconds()
            if elapsed_time > self.resource_limits["max_execution_time"]:
                logger.warning(f"执行时间超过限制: {elapsed_time:.2f}秒")
                return False

        return True
```

### 5. 日志安全
**当前问题：**
- 日志中可能包含敏感信息
- 缺乏日志级别控制

**改进建议：**
```python
def _sanitize_log_message(self, message: str) -> str:
    """清理日志消息中的敏感信息"""
    import re

    # 移除可能的密码信息
    message = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?', 'password=***', message, flags=re.IGNORECASE)

    # 移除可能的连接字符串
    message = re.sub(r'://[^@]+@[^/\s]+', '://***@***', message)

    return message

def _log_securely(self, level: str, message: str):
    """安全日志记录"""
    sanitized_message = self._sanitize_log_message(message)
    getattr(logger, level)(sanitized_message)
```

### 6. 配置安全
**当前问题：**
- 配置文件可能包含敏感信息
- 缺乏配置验证

**改进建议：**
```python
def _validate_config(self, config: Dict[str, Any]) -> bool:
    """验证配置安全性"""
    required_fields = ["global", "tables"]

    # 检查必需字段
    for field in required_fields:
        if field not in config:
            raise ValueError(f"配置缺少必需字段: {field}")

    # 验证全局配置
    global_config = config.get("global", {})
    if global_config.get("max_execution_time", 0) > 7200:  # 最大2小时
        raise ValueError("执行时间限制过长")

    # 验证表配置
    for table_config in config.get("tables", []):
        if not table_config.get("name"):
            raise ValueError("表配置缺少表名")
        if not table_config.get("date_column"):
            raise ValueError("表配置缺少日期字段")

    return True

def _load_config(self, config_file: str) -> Dict[str, Any]:
    """安全加载配置"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 验证配置
        if not self._validate_config(config):
            raise ValueError("配置验证失败")

        logger.info(f"成功加载清理规则配置: {config_file}")
        return config
    except Exception as e:
        logger.error(f"加载清理规则配置失败: {e}")
        raise
```

### 7. 错误处理改进
**当前问题：**
- 错误信息可能泄露敏感信息
- 缺乏错误分类

**改进建议：**
```python
class CleanupError(Exception):
    """清理操作异常基类"""
    pass

class PermissionError(CleanupError):
    """权限错误"""
    pass

class ResourceLimitError(CleanupError):
    """资源限制错误"""
    pass

def _handle_error(self, error: Exception, context: str):
    """统一错误处理"""
    if isinstance(error, PermissionError):
        logger.error(f"权限错误: {context}")
        self.execution_stats["errors"].append(f"权限错误: {context}")
    elif isinstance(error, ResourceLimitError):
        logger.error(f"资源限制: {context}")
        self.execution_stats["errors"].append(f"资源限制: {context}")
    else:
        # 不记录详细错误信息，避免信息泄露
        logger.error(f"操作失败: {context}")
        self.execution_stats["errors"].append(f"操作失败: {context}")
```

## 🛡️ 安全最佳实践

### 1. 最小权限原则
- 数据库用户只具有必要的DELETE权限
- 定期审查和更新权限

### 2. 审计和监控
- 记录所有清理操作的详细日志
- 实现操作审计功能

### 3. 备份策略
- 清理前自动创建备份
- 实现备份验证机制

### 4. 测试环境
- 在生产环境执行前在测试环境验证
- 使用相同的数据结构进行测试

### 5. 监控和告警
- 监控清理操作的执行状态
- 设置异常情况告警

## 📋 实施优先级

### 高优先级（立即实施）
1. SQL注入防护
2. 事务管理改进
3. 权限验证

### 中优先级（近期实施）
4. 资源限制
5. 日志安全
6. 配置验证

### 低优先级（长期规划）
7. 审计功能
8. 备份策略
9. 监控告警

## 🔧 实施建议

1. **分阶段实施**：按照优先级逐步改进
2. **充分测试**：每个改进都要在测试环境验证
3. **文档更新**：及时更新相关文档
4. **团队培训**：确保团队了解安全最佳实践
5. **定期审查**：定期审查和改进安全措施
