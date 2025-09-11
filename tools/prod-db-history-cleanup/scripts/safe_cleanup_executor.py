#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全清理执行器模块
使用ID分页和事务保护，确保基于ID的清理操作的安全性和一致性
"""

import yaml
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
import os
from tqdm import tqdm


# 动态导入模块
def import_db_connector():
    """动态导入数据库连接器模块"""
    try:
        from .db_connector import DatabaseConnector, DatabaseMonitor
    except ImportError:
        try:
            from scripts.db_connector import DatabaseConnector, DatabaseMonitor
        except ImportError:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from db_connector import DatabaseConnector, DatabaseMonitor

    return DatabaseConnector, DatabaseMonitor


DatabaseConnector, DatabaseMonitor = import_db_connector()

logger = logging.getLogger(__name__)


class SafeCleanupExecutor:
    """安全清理执行器"""

    def __init__(self, db_connector: DatabaseConnector, config_file: str):
        """
        初始化安全清理执行器

        Args:
            db_connector: 数据库连接器
            config_file: 清理规则配置文件
        """
        self.db_connector = db_connector
        self.monitor = DatabaseMonitor(db_connector)
        self.config = self._load_config(config_file)
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "tables_processed": 0,
            "total_records_cleaned": 0,
            "total_space_saved_mb": 0,
            "errors": [],
            "warnings": [],
            "safety_checks_passed": 0,
            "safety_checks_failed": 0,
            "max_ids_before_cleanup": {},  # 记录每张表清理前的最大ID
        }

        # 资源限制配置
        self.resource_limits = {
            "max_memory_mb": 1024,  # 最大内存使用 (MB)
            "max_execution_time": 3600,  # 最大执行时间 (秒)
            "max_batch_size": 5000,  # 最大批次大小
            "connection_timeout": 30,  # 连接超时 (秒)
        }

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载清理规则配置"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载清理规则配置: {config_file}")
            return config
        except Exception as e:
            logger.error(f"加载清理规则配置失败: {e}")
            raise

    def _get_table_primary_key(self, table_name: str) -> Optional[str]:
        """获取表的主键字段名"""
        try:
            sql = """
                SELECT COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND CONSTRAINT_NAME = 'PRIMARY'
                AND ORDINAL_POSITION = 1
            """
            result = self.db_connector.execute_query(
                sql, (self.db_connector.config["database"]["database"], table_name)
            )

            if result:
                primary_key = result[0]["COLUMN_NAME"]
                logger.info(f"表 {table_name} 的主键: {primary_key}")
                return primary_key
            else:
                logger.warning(f"表 {table_name} 没有找到主键")
                return None

        except Exception as e:
            logger.error(f"获取表 {table_name} 主键失败: {e}")
            return None

    def _get_table_indexes(self, table_name: str) -> List[str]:
        """获取表的索引字段"""
        try:
            sql = """
                SELECT COLUMN_NAME
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND INDEX_NAME != 'PRIMARY'
                ORDER BY SEQ_IN_INDEX
            """
            result = self.db_connector.execute_query(
                sql, (self.db_connector.config["database"]["database"], table_name)
            )

            indexes = [row["COLUMN_NAME"] for row in result]
            logger.info(f"表 {table_name} 的索引字段: {indexes}")
            return indexes

        except Exception as e:
            logger.error(f"获取表 {table_name} 索引失败: {e}")
            return []

    def _validate_identifier(self, identifier: str) -> bool:
        """验证标识符是否安全，防止SQL注入"""
        import re

        # 只允许字母、数字、下划线，且必须以字母或下划线开头
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))

    def _check_resource_usage(self) -> bool:
        """检查资源使用情况"""
        try:
            import psutil

            # 检查内存使用
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            if memory_usage > self.resource_limits["max_memory_mb"]:
                logger.warning(
                    f"内存使用超过限制: {memory_usage:.2f}MB > {self.resource_limits['max_memory_mb']}MB"
                )
                return False

            # 检查执行时间
            if self.execution_stats["start_time"]:
                elapsed_time = (
                    datetime.now() - self.execution_stats["start_time"]
                ).total_seconds()
                if elapsed_time > self.resource_limits["max_execution_time"]:
                    logger.warning(
                        f"执行时间超过限制: {elapsed_time:.2f}秒 > {self.resource_limits['max_execution_time']}秒"
                    )
                    return False

            return True
        except ImportError:
            # 如果没有psutil，跳过内存检查
            logger.debug("psutil未安装，跳过内存使用检查")
            return True
        except Exception as e:
            logger.warning(f"资源检查失败: {e}")
            return True

    def _sanitize_log_message(self, message: str) -> str:
        """清理日志消息中的敏感信息"""
        import re

        # 移除可能的密码信息
        message = re.sub(
            r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
            "password=***",
            message,
            flags=re.IGNORECASE,
        )

        # 移除可能的连接字符串
        message = re.sub(r"://[^@]+@[^/\s]+", "://***@***", message)

        # 移除可能的API密钥
        message = re.sub(
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
            "api_key=***",
            message,
            flags=re.IGNORECASE,
        )

        return message

    def _log_securely(self, level: str, message: str):
        """安全日志记录"""
        sanitized_message = self._sanitize_log_message(message)
        getattr(logger, level)(sanitized_message)

    def _get_max_id_before_cleanup(self, table_name: str, max_id: int) -> Optional[int]:
        """获取清理前符合条件的最大ID"""
        try:
            # 验证表名，防止SQL注入
            if not self._validate_identifier(table_name):
                logger.error(f"无效的表名: {table_name}")
                return None

            sql = f"""
                SELECT MAX(id) as max_id
                FROM {table_name}
                WHERE id < %s
            """
            result = self.db_connector.execute_query(sql, (max_id,))

            if result and result[0]["max_id"] is not None:
                actual_max_id = int(result[0]["max_id"])
                logger.info(
                    f"表 {table_name} 执行清理的最大ID: {actual_max_id:,} (清理 ID < {max_id:,} 的记录)"
                )
                return actual_max_id
            else:
                logger.info(f"表 {table_name} 没有符合条件的记录需要清理")
                return None

        except Exception as e:
            logger.error(f"获取表 {table_name} 清理前最大ID失败: {e}")
            return None

    def _get_min_id_before_cleanup(self, table_name: str, max_id: int) -> Optional[int]:
        """获取清理前符合条件的最小ID"""
        try:
            # 验证表名，防止SQL注入
            if not self._validate_identifier(table_name):
                logger.error(f"无效的表名: {table_name}")
                return None

            sql = f"""
                SELECT MIN(id) as min_id
                FROM {table_name}
                WHERE id < %s
            """
            result = self.db_connector.execute_query(sql, (max_id,))

            if result and result[0]["min_id"] is not None:
                min_id = int(result[0]["min_id"])
                logger.info(f"表 {table_name} 执行清理的最小ID: {min_id:,}")
                return min_id
            else:
                logger.info(f"表 {table_name} 没有符合条件的记录需要清理")
                return None

        except Exception as e:
            logger.error(f"获取表 {table_name} 清理前最小ID失败: {e}")
            return None

    def _validate_table_structure(self, table_name: str, max_id: int) -> Dict[str, Any]:
        """验证表结构是否适合安全清理"""
        validation_result = {
            "is_safe": False,
            "primary_key": None,
            "recommended_approach": None,
            "warnings": [],
            "errors": [],
        }

        try:
            # 1. 检查主键
            primary_key = self._get_table_primary_key(table_name)
            if not primary_key:
                validation_result["errors"].append("表没有主键，无法进行安全清理")
                validation_result["recommended_approach"] = "manual_review"
                return validation_result

            # 打印日志，提醒用户主键不管是什么字段，都使用id作为主键进行删除
            logger.warning(
                f"表 {table_name} 的主键是 {primary_key}，但不管是什么字段，都使用id作为主键进行删除"
            )
            validation_result["primary_key"] = "id"

            # 2. 检查ID字段是否有索引
            indexes = self._get_table_indexes(table_name)
            if "id" not in indexes:
                validation_result["warnings"].append("ID字段没有索引，可能影响性能")

            # 3. 检查表大小
            size_info = self.monitor.check_table_size(table_name)
            table_size_mb = size_info.get("Size_MB", 0)

            if table_size_mb > 1000:  # 大于1GB
                validation_result["warnings"].append(
                    f"表大小较大 ({table_size_mb:.2f}MB)，建议在低峰期执行"
                )

            # 4. 检查是否有外键约束
            fk_sql = """
                SELECT COUNT(*) as fk_count
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            fk_result = self.db_connector.execute_query(
                fk_sql, (self.db_connector.config["database"]["database"], table_name)
            )

            if fk_result and fk_result[0]["fk_count"] > 0:
                validation_result["warnings"].append(
                    "表存在外键约束，删除前请确认不会影响其他表"
                )

            # 5. 检查ID字段的数据类型
            column_sql = """
                SELECT DATA_TYPE, IS_NULLABLE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                AND COLUMN_NAME = 'id'
            """
            column_result = self.db_connector.execute_query(
                column_sql,
                (
                    self.db_connector.config["database"]["database"],
                    table_name,
                ),
            )

            if column_result:
                data_type = column_result[0]["DATA_TYPE"]
                is_nullable = column_result[0]["IS_NULLABLE"] == "YES"

                if data_type not in ["int", "bigint", "mediumint", "smallint"]:
                    validation_result["warnings"].append(
                        f"ID字段类型为 {data_type}，请确认字段选择正确"
                    )

                if is_nullable:
                    validation_result["warnings"].append(
                        "ID字段允许NULL值，可能影响清理逻辑"
                    )

            # 6. 检查配置的max_id是否合理
            current_max_id_sql = f"SELECT MAX(id) as max_id FROM {table_name}"
            current_max_result = self.db_connector.execute_query(current_max_id_sql)

            if current_max_result and current_max_result[0]["max_id"] is not None:
                current_max_table_id = int(current_max_result[0]["max_id"])
                if max_id > current_max_table_id:
                    validation_result["warnings"].append(
                        f"配置的max_id ({max_id:,}) 大于表当前最大ID ({current_max_table_id:,})，可能不会清理任何数据"
                    )
                elif max_id == current_max_table_id:
                    validation_result["warnings"].append(
                        f"配置的max_id ({max_id:,}) 等于表当前最大ID，可能清理所有数据，请确认"
                    )

            # 如果通过所有检查，标记为安全
            if not validation_result["errors"]:
                validation_result["is_safe"] = True
                validation_result["recommended_approach"] = "id_based_pagination"

        except Exception as e:
            validation_result["errors"].append(f"验证表结构时出错: {e}")

        return validation_result

    def _safe_delete_batch_by_id(
        self,
        table_name: str,
        max_id: int,
        batch_size: int,
        last_id: Optional[int] = None,
    ) -> Tuple[int, Optional[int]]:
        """
        使用ID分页安全删除一批数据

        Returns:
            Tuple[int, Optional[int]]: (删除的记录数, 最后处理的ID)
        """
        try:
            # 验证表名，防止SQL注入
            if not self._validate_identifier(table_name):
                logger.error(f"无效的表名: {table_name}")
                return 0, last_id

            # 构建WHERE条件
            where_conditions = ["id < %s"]
            params = [max_id]

            if last_id is not None:
                where_conditions.append("id >= %s")  # 修复：使用 >= 确保不跳过记录
                params.append(last_id)

            where_clause = " AND ".join(where_conditions)

            # 执行删除
            delete_sql = f"""
                DELETE FROM {table_name}
                WHERE {where_clause}
                ORDER BY id
                LIMIT %s
            """
            params.append(batch_size)

            # 添加调试日志
            logger.debug(f"执行删除SQL: {delete_sql}")
            logger.debug(f"参数: {params}")
            logger.debug(f"当前last_id: {last_id}")
            logger.debug(f"max_id: {max_id}")

            # 额外的安全检查：确保不会删除比max_id大的记录
            if last_id is not None and last_id >= max_id:
                logger.warning(
                    f"安全警告：last_id ({last_id}) >= max_id ({max_id})，跳过此批次删除"
                )
                return 0, last_id

            affected_rows = self.db_connector.execute_update(delete_sql, params)
            logger.debug(f"删除影响行数: {affected_rows}")

            # 获取最后处理的ID - 修复：获取剩余记录中的最小ID作为下一轮的起始点
            if affected_rows > 0:
                # 修复：获取剩余记录中的最小ID，作为下一轮的起始点
                # 这样可以确保下一轮从正确的位置开始，不会跳过记录
                remaining_min_id_sql = f"""
                    SELECT MIN(id) as min_id
                    FROM {table_name}
                    WHERE id < %s
                """
                remaining_result = self.db_connector.execute_query(
                    remaining_min_id_sql, (max_id,)
                )
                if remaining_result and remaining_result[0]["min_id"] is not None:
                    last_processed_id = int(remaining_result[0]["min_id"])
                    logger.debug(f"剩余记录最小ID: {last_processed_id}")
                else:
                    # 如果没有剩余记录，说明已经清理完毕
                    last_processed_id = max_id
                    logger.debug(f"无剩余记录，设置last_processed_id为max_id: {max_id}")
            else:
                # 如果没有删除任何记录，说明已经清理完毕
                last_processed_id = max_id
                logger.debug(f"未删除记录，设置last_processed_id为max_id: {max_id}")

            logger.debug(f"下一轮last_processed_id: {last_processed_id}")
            return affected_rows, last_processed_id

        except Exception as e:
            logger.error(f"安全删除批次失败: {e}")
            raise

    def execute_safe_cleanup(
        self, dry_run: bool = False, table_name: str = None
    ) -> Dict[str, Any]:
        """
        执行安全清理操作

        Args:
            dry_run: 是否试运行
            table_name: 指定表名，如果为None则清理所有表

        Returns:
            Dict: 执行结果
        """
        self.execution_stats["start_time"] = datetime.now()
        logger.info(f"开始执行安全清理操作 (dry_run={dry_run})")

        if dry_run:
            logger.info("试运行模式：不会实际删除数据")

        try:
            # 获取需要清理的表
            tables_to_cleanup = self._get_tables_to_cleanup(table_name)

            if not tables_to_cleanup:
                logger.warning("没有找到需要清理的表")
                return self.execution_stats

            # 执行清理
            for table_config in tables_to_cleanup:
                self._safe_cleanup_table(table_config, dry_run)

            self.execution_stats["end_time"] = datetime.now()
            self._log_execution_summary()

            return self.execution_stats

        except Exception as e:
            logger.error(f"安全清理执行失败: {e}")
            self.execution_stats["errors"].append(str(e))
            raise

    def _get_tables_to_cleanup(self, table_name: str = None) -> List[Dict[str, Any]]:
        """获取需要清理的表列表"""
        tables = []

        for table_config in self.config.get("tables", []):
            if not table_config.get("enabled", True):
                continue

            if table_name and table_config["name"] != table_name:
                continue

            # 检查表是否存在
            table_info = self.db_connector.get_table_info(table_config["name"])
            if not table_info:
                logger.warning(f"表 {table_config['name']} 不存在，跳过")
                continue

            # 检查是否配置了max_id
            if "max_id" not in table_config:
                logger.warning(f"表 {table_config['name']} 未配置max_id，跳过")
                continue

            tables.append(table_config)

        return tables

    def _safe_cleanup_table(self, table_config: Dict[str, Any], dry_run: bool):
        """安全清理单个表"""
        table_name = table_config["name"]
        max_id = table_config["max_id"]
        batch_size = table_config.get("batch_size", 1000)

        logger.info(f"开始安全清理表: {table_name}")

        try:
            # 验证表结构
            validation_result = self._validate_table_structure(table_name, max_id)

            if not validation_result["is_safe"]:
                error_msg = (
                    f"表 {table_name} 结构验证失败: {validation_result['errors']}"
                )
                logger.error(error_msg)
                self.execution_stats["errors"].append(error_msg)
                self.execution_stats["safety_checks_failed"] += 1
                return

            self.execution_stats["safety_checks_passed"] += 1

            # 记录清理前的最大ID
            # max_id_before = self._get_max_id_before_cleanup(table_name, max_id)
            # if max_id_before is not None:
            #     self.execution_stats["max_ids_before_cleanup"][
            #         table_name
            #     ] = max_id_before

            # 获取需要清理的记录数
            count_sql = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE id < %s
            """
            count_result = self.db_connector.execute_query(count_sql, (max_id,))
            total_records = count_result[0]["count"] if count_result else 0

            if total_records == 0:
                logger.info(f"表 {table_name} 无需清理")
                return

            logger.info(
                f"表 {table_name} 需要清理 {total_records:,} 条记录 (ID < {max_id:,})"
            )

            # 获取表大小信息
            size_before = self.monitor.check_table_size(table_name)

            # 执行清理
            if dry_run:
                self._simulate_safe_cleanup(
                    table_name, max_id, total_records, batch_size
                )
            else:
                self._perform_safe_cleanup(
                    table_name, max_id, total_records, batch_size
                )

            # 获取清理后的表大小
            size_after = self.monitor.check_table_size(table_name)

            # 计算节省的空间
            space_saved = size_before.get("Size_MB", 0) - size_after.get("Size_MB", 0)

            # 更新统计信息
            self.execution_stats["tables_processed"] += 1
            self.execution_stats["total_records_cleaned"] += total_records
            self.execution_stats["total_space_saved_mb"] += space_saved

            logger.info(f"表 {table_name} 安全清理完成，节省空间: {space_saved:.2f}MB")

        except Exception as e:
            error_msg = f"安全清理表 {table_name} 失败: {e}"
            logger.error(error_msg)
            self.execution_stats["errors"].append(error_msg)
            raise

    def _simulate_safe_cleanup(
        self,
        table_name: str,
        max_id: int,
        total_records: int,
        batch_size: int,
    ):
        """模拟安全清理过程"""
        logger.info(f"模拟安全清理表 {table_name}")

        # 计算批次数
        total_batches = (total_records + batch_size - 1) // batch_size

        with tqdm(total=total_batches, desc=f"模拟安全清理 {table_name}") as pbar:
            for batch_num in range(total_batches):
                # 模拟处理时间
                time.sleep(0.1)

                # 更新进度
                pbar.update(1)
                pbar.set_postfix(
                    {
                        "batch": f"{batch_num + 1}/{total_batches}",
                        "records": f"{min((batch_num + 1) * batch_size, total_records):,}",
                    }
                )

                # 检查是否需要休眠
                if batch_num > 0 and batch_num % 10 == 0:
                    time.sleep(self.config["global"].get("sleep_between_batches", 1))

        logger.info(f"模拟安全清理完成: {table_name} - {total_records:,} 条记录")

    def _perform_safe_cleanup(
        self,
        table_name: str,
        max_id: int,
        total_records: int,
        batch_size: int,
    ):
        """执行实际安全清理"""
        logger.info(f"开始实际安全清理表 {table_name}")

        records_cleaned = 0
        last_processed_id = None

        # 修复：使用基于实际数据存在性的循环，而不是基于预估批次数
        batch_num = 0
        while True:
            try:
                # 检查资源使用情况
                if not self._check_resource_usage():
                    logger.warning(f"资源使用超过限制，停止清理表 {table_name}")
                    break

                # 检查执行时间限制
                if self._check_time_limit():
                    logger.warning(f"达到最大执行时间限制，停止清理表 {table_name}")
                    break

                # 检查是否还有需要清理的数据
                if last_processed_id is not None:
                    remaining_count_sql = f"""
                        SELECT COUNT(*) as count
                        FROM {table_name}
                        WHERE id >= %s AND id < %s
                    """
                    remaining_result = self.db_connector.execute_query(
                        remaining_count_sql, (last_processed_id, max_id)
                    )
                    remaining_count = (
                        remaining_result[0]["count"] if remaining_result else 0
                    )

                    if remaining_count == 0:
                        logger.info(f"表 {table_name} 已无更多数据需要清理，停止循环")
                        break

                # 执行批量删除
                batch_records, last_processed_id = self._safe_delete_batch_by_id(
                    table_name, max_id, batch_size, last_processed_id
                )

                if batch_records == 0:
                    logger.info(
                        f"表 {table_name} 批次 {batch_num + 1} 未删除任何记录，停止循环"
                    )
                    break

                records_cleaned += batch_records
                batch_num += 1

                # 输出进度信息
                logger.info(
                    f"表 {table_name} 批次 {batch_num}: 删除 {batch_records:,} 条记录，"
                    f"累计删除 {records_cleaned:,} 条记录"
                )

                # 检查是否需要休眠
                if batch_num > 0 and batch_num % 10 == 0:
                    sleep_time = self.config["global"].get("sleep_between_batches", 1)
                    logger.debug(f"休眠 {sleep_time} 秒")
                    time.sleep(sleep_time)

            except Exception as e:
                error_msg = f"安全清理批次 {batch_num + 1} 失败: {e}"
                logger.error(error_msg)
                self.execution_stats["errors"].append(error_msg)

                # 根据配置决定是否继续
                if (
                    not self.config.get("cleanup_strategy", {})
                    .get("error_handling", {})
                    .get("continue_on_error", False)
                ):
                    raise

        logger.info(
            f"表 {table_name} 安全清理完成，实际清理 {records_cleaned:,} 条记录"
        )

    def _check_time_limit(self) -> bool:
        """检查是否达到时间限制"""
        if not self.execution_stats["start_time"]:
            return False

        max_execution_time = self.config["global"].get("max_execution_time", 3600)
        elapsed_time = (
            datetime.now() - self.execution_stats["start_time"]
        ).total_seconds()

        return elapsed_time >= max_execution_time

    def _log_execution_summary(self):
        """记录执行摘要"""
        if not self.execution_stats["end_time"]:
            return

        duration = (
            self.execution_stats["end_time"] - self.execution_stats["start_time"]
        ).total_seconds()

        logger.info("=" * 60)
        logger.info("安全清理执行摘要")
        logger.info("=" * 60)
        logger.info(f"执行时间: {duration:.2f} 秒")
        logger.info(f"处理表数: {self.execution_stats['tables_processed']}")
        logger.info(f"清理记录数: {self.execution_stats['total_records_cleaned']:,}")
        logger.info(f"节省空间: {self.execution_stats['total_space_saved_mb']:.2f}MB")
        logger.info(f"安全检查通过: {self.execution_stats['safety_checks_passed']}")
        logger.info(f"安全检查失败: {self.execution_stats['safety_checks_failed']}")

        if self.execution_stats["errors"]:
            logger.warning(f"错误数量: {len(self.execution_stats['errors'])}")
            for error in self.execution_stats["errors"]:
                logger.warning(f"  - {error}")

        if self.execution_stats["warnings"]:
            logger.warning(f"警告数量: {len(self.execution_stats['warnings'])}")
            for warning in self.execution_stats["warnings"]:
                logger.warning(f"  - {warning}")

        logger.info("=" * 60)

    def verify_safe_cleanup(self, table_name: str = None) -> Dict[str, Any]:
        """
        验证安全清理结果

        Args:
            table_name: 指定表名，如果为None则验证所有表

        Returns:
            Dict: 验证结果
        """
        logger.info("开始验证安全清理结果")

        verification_results = {
            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables_verified": 0,
            "verification_passed": 0,
            "verification_failed": 0,
            "details": {},
        }

        try:
            tables_to_verify = self._get_tables_to_cleanup(table_name)

            for table_config in tables_to_verify:
                table_name = table_config["name"]
                max_id = table_config["max_id"]

                logger.info(f"验证表: {table_name}")

                # 检查是否还有需要清理的数据
                check_sql = f"""
                    SELECT COUNT(*) as count
                    FROM {table_name}
                    WHERE id < %s
                """
                result = self.db_connector.execute_query(check_sql, (max_id,))
                remaining_count = result[0]["count"] if result else 0

                verification_results["tables_verified"] += 1

                if remaining_count == 0:
                    verification_results["verification_passed"] += 1
                    logger.info(f"表 {table_name} 验证通过")
                    verification_results["details"][table_name] = {
                        "status": "passed",
                        "remaining_records": 0,
                    }
                else:
                    verification_results["verification_failed"] += 1
                    logger.warning(
                        f"表 {table_name} 验证失败，仍有 {remaining_count} 条记录需要清理"
                    )
                    verification_results["details"][table_name] = {
                        "status": "failed",
                        "remaining_records": remaining_count,
                    }

        except Exception as e:
            logger.error(f"验证安全清理结果失败: {e}")
            verification_results["errors"] = str(e)

        return verification_results

    def get_safe_cleanup_preview(self, table_name: str = None) -> Dict[str, Any]:
        """
        获取安全清理预览信息

        Args:
            table_name: 指定表名，如果为None则预览所有表

        Returns:
            Dict: 预览信息
        """
        logger.info("开始获取安全清理预览信息")

        preview_results = {
            "preview_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables_previewed": 0,
            "total_records_to_clean": 0,
            "estimated_space_saved_mb": 0,
            "safety_checks_passed": 0,
            "safety_checks_failed": 0,
            "details": {},
        }

        try:
            tables_to_preview = self._get_tables_to_cleanup(table_name)

            for table_config in tables_to_preview:
                table_name = table_config["name"]
                max_id = table_config["max_id"]

                logger.info(f"预览表: {table_name}")

                # 验证表结构
                validation_result = self._validate_table_structure(table_name, max_id)

                if validation_result["is_safe"]:
                    preview_results["safety_checks_passed"] += 1
                else:
                    preview_results["safety_checks_failed"] += 1

                # 获取需要清理的记录数
                count_sql = f"""
                    SELECT COUNT(*) as count
                    FROM {table_name}
                    WHERE id < %s
                """
                result = self.db_connector.execute_query(count_sql, (max_id,))
                records_to_clean = result[0]["count"] if result else 0

                # 获取表大小信息
                table_size = self.monitor.check_table_size(table_name)
                current_size_mb = table_size.get("Size_MB", 0)

                # 估算清理后的大小（简单估算）
                total_records_sql = f"SELECT COUNT(*) as count FROM {table_name}"
                total_result = self.db_connector.execute_query(total_records_sql)
                total_records = total_result[0]["count"] if total_result else 0

                if total_records > 0:
                    avg_record_size_mb = current_size_mb / total_records
                    estimated_space_saved = records_to_clean * avg_record_size_mb
                else:
                    estimated_space_saved = 0

                preview_results["tables_previewed"] += 1
                preview_results["total_records_to_clean"] += records_to_clean
                preview_results["estimated_space_saved_mb"] += estimated_space_saved

                preview_results["details"][table_name] = {
                    "max_id": max_id,
                    "records_to_clean": records_to_clean,
                    "current_size_mb": current_size_mb,
                    "estimated_space_saved_mb": estimated_space_saved,
                    "is_safe": validation_result["is_safe"],
                    "warnings": validation_result.get("warnings", []),
                    "errors": validation_result.get("errors", []),
                }

                logger.info(
                    f"表 {table_name}: 将清理 {records_to_clean:,} 条记录，预计节省 {estimated_space_saved:.2f}MB"
                )

        except Exception as e:
            logger.error(f"获取安全清理预览信息失败: {e}")
            preview_results["errors"] = str(e)

        return preview_results


if __name__ == "__main__":
    # 测试代码
    import logging

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试安全清理执行器
    db_connector = DatabaseConnector("config/database.yaml")
    executor = SafeCleanupExecutor(db_connector, "config/cleanup-rules.yaml")

    # 试运行
    results = executor.execute_safe_cleanup(dry_run=True)
    print(f"安全试运行结果: {results}")

    db_connector.close()
