#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理执行器模块
提供安全、高效的基于ID的数据清理执行功能
@deprecated 使用 safe_cleanup_executor.py 替代
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
        # 方式1：相对导入
        from .db_connector import DatabaseConnector, DatabaseMonitor
    except ImportError:
        try:
            # 方式2：绝对导入
            from scripts.db_connector import DatabaseConnector, DatabaseMonitor
        except ImportError:
            # 方式3：直接导入
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from db_connector import DatabaseConnector, DatabaseMonitor

    return DatabaseConnector, DatabaseMonitor


# 导入模块
DatabaseConnector, DatabaseMonitor = import_db_connector()

logger = logging.getLogger(__name__)


class CleanupExecutor:
    """清理执行器"""

    def __init__(self, db_connector: DatabaseConnector, config_file: str):
        """
        初始化清理执行器

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

    def execute_cleanup(
        self, dry_run: bool = False, table_name: str = None
    ) -> Dict[str, Any]:
        """
        执行清理操作

        Args:
            dry_run: 是否试运行
            table_name: 指定表名，如果为None则清理所有表

        Returns:
            Dict: 执行结果
        """
        self.execution_stats["start_time"] = datetime.now()
        logger.info(f"开始执行清理操作 (dry_run={dry_run})")

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
                self._cleanup_table(table_config, dry_run)

            self.execution_stats["end_time"] = datetime.now()
            self._log_execution_summary()

            return self.execution_stats

        except Exception as e:
            logger.error(f"清理执行失败: {e}")
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

    def _cleanup_table(self, table_config: Dict[str, Any], dry_run: bool):
        """清理单个表"""
        table_name = table_config["name"]
        max_id = table_config["max_id"]
        batch_size = table_config.get("batch_size", 1000)

        logger.info(f"开始清理表: {table_name}")

        try:
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

            logger.info(f"表 {table_name} 需要清理 {total_records:,} 条记录 (ID < {max_id})")

            # 获取表大小信息
            size_before = self.monitor.check_table_size(table_name)

            # 执行清理
            if dry_run:
                self._simulate_cleanup(
                    table_name, max_id, total_records, batch_size
                )
            else:
                self._perform_cleanup(
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

            logger.info(f"表 {table_name} 清理完成，节省空间: {space_saved:.2f}MB")

        except Exception as e:
            error_msg = f"清理表 {table_name} 失败: {e}"
            logger.error(error_msg)
            self.execution_stats["errors"].append(error_msg)
            raise

    def _simulate_cleanup(
        self,
        table_name: str,
        max_id: int,
        total_records: int,
        batch_size: int,
    ):
        """模拟清理过程，将实际清理过程替换为模拟清理过程（sleep 0.1秒），实际清理过程在_perform_cleanup方法中"""
        logger.info(f"模拟清理表 {table_name}")

        # 计算批次数
        total_batches = (total_records + batch_size - 1) // batch_size

        with tqdm(total=total_batches, desc=f"模拟清理 {table_name}") as pbar:
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

        logger.info(f"模拟清理完成: {table_name} - {total_records:,} 条记录")

    def _perform_cleanup(
        self,
        table_name: str,
        max_id: int,
        total_records: int,
        batch_size: int,
    ):
        """执行实际清理"""
        logger.info(f"开始实际清理表 {table_name}")

        # 计算批次数
        total_batches = (total_records + batch_size - 1) // batch_size
        records_cleaned = 0

        with tqdm(total=total_batches, desc=f"清理 {table_name}") as pbar:
            for batch_num in range(total_batches):
                try:
                    # 执行批量删除
                    batch_records = self._delete_batch(
                        table_name, max_id, batch_size
                    )
                    records_cleaned += batch_records

                    # 更新进度
                    pbar.update(1)
                    pbar.set_postfix(
                        {
                            "batch": f"{batch_num + 1}/{total_batches}",
                            "cleaned": f"{records_cleaned:,}",
                            "remaining": f"{total_records - records_cleaned:,}",
                        }
                    )

                    # 检查是否需要休眠
                    if batch_num > 0 and batch_num % 10 == 0:
                        sleep_time = self.config["global"].get(
                            "sleep_between_batches", 1
                        )
                        logger.debug(f"休眠 {sleep_time} 秒")
                        time.sleep(sleep_time)

                    # 检查执行时间限制
                    if self._check_time_limit():
                        logger.warning(f"达到最大执行时间限制，停止清理表 {table_name}")
                        break

                except Exception as e:
                    error_msg = f"清理批次 {batch_num + 1} 失败: {e}"
                    logger.error(error_msg)
                    self.execution_stats["errors"].append(error_msg)

                    # 根据配置决定是否继续
                    if (
                        not self.config.get("cleanup_strategy", {})
                        .get("error_handling", {})
                        .get("continue_on_error", False)
                    ):
                        raise

        logger.info(f"表 {table_name} 清理完成，实际清理 {records_cleaned:,} 条记录")

    def _delete_batch(
        self, table_name: str, max_id: int, batch_size: int
    ) -> int:
        """删除一批数据"""
        try:
            # 使用LIMIT和ORDER BY确保稳定的批量删除
            delete_sql = f"""
                DELETE FROM {table_name}
                WHERE id < %s
                ORDER BY id
                LIMIT %s
            """

            affected_rows = self.db_connector.execute_update(
                delete_sql, (max_id, batch_size)
            )
            return affected_rows

        except Exception as e:
            logger.error(f"批量删除失败: {e}")
            raise

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
        logger.info("清理执行摘要")
        logger.info("=" * 60)
        logger.info(f"执行时间: {duration:.2f} 秒")
        logger.info(f"处理表数: {self.execution_stats['tables_processed']}")
        logger.info(f"清理记录数: {self.execution_stats['total_records_cleaned']:,}")
        logger.info(f"节省空间: {self.execution_stats['total_space_saved_mb']:.2f}MB")

        if self.execution_stats["errors"]:
            logger.warning(f"错误数量: {len(self.execution_stats['errors'])}")
            for error in self.execution_stats["errors"]:
                logger.warning(f"  - {error}")

        if self.execution_stats["warnings"]:
            logger.warning(f"警告数量: {len(self.execution_stats['warnings'])}")
            for warning in self.execution_stats["warnings"]:
                logger.warning(f"  - {warning}")

        logger.info("=" * 60)

    def verify_cleanup(self, table_name: str = None) -> Dict[str, Any]:
        """
        验证清理结果

        Args:
            table_name: 指定表名，如果为None则验证所有表

        Returns:
            Dict: 验证结果
        """
        logger.info("开始验证清理结果")

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
                    logger.warning(f"表 {table_name} 验证失败，仍有 {remaining_count} 条记录需要清理")
                    verification_results["details"][table_name] = {
                        "status": "failed",
                        "remaining_records": remaining_count,
                    }

        except Exception as e:
            logger.error(f"验证清理结果失败: {e}")
            verification_results["errors"] = str(e)

        return verification_results

    def get_cleanup_preview(self, table_name: str = None) -> Dict[str, Any]:
        """
        获取清理预览信息

        Args:
            table_name: 指定表名，如果为None则预览所有表

        Returns:
            Dict: 预览信息
        """
        logger.info("开始获取清理预览信息")

        preview_results = {
            "preview_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables_previewed": 0,
            "total_records_to_clean": 0,
            "estimated_space_saved_mb": 0,
            "details": {},
        }

        try:
            tables_to_preview = self._get_tables_to_cleanup(table_name)

            for table_config in tables_to_preview:
                table_name = table_config["name"]
                max_id = table_config["max_id"]

                logger.info(f"预览表: {table_name}")

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
                }

                logger.info(f"表 {table_name}: 将清理 {records_to_clean:,} 条记录，预计节省 {estimated_space_saved:.2f}MB")

        except Exception as e:
            logger.error(f"获取清理预览信息失败: {e}")
            preview_results["errors"] = str(e)

        return preview_results


if __name__ == "__main__":
    # 测试代码
    import logging

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试清理执行器
    db_connector = DatabaseConnector("config/database.yaml")
    executor = CleanupExecutor(db_connector, "config/cleanup-rules.yaml")

    # 试运行
    results = executor.execute_cleanup(dry_run=True)
    print(f"试运行结果: {results}")

    # 验证结果
    verification = executor.verify_cleanup()
    print(f"验证结果: {verification}")

    db_connector.close()
