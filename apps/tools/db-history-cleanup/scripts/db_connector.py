#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理模块
提供数据库连接池、连接管理和错误处理功能
"""

import logging
import ssl
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

import pymysql
import yaml
from dbutils.pooled_db import PooledDB
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """数据库连接管理器"""

    def __init__(self, config_file: str):
        """
        初始化数据库连接管理器

        Args:
            config_file: 数据库配置文件路径
        """
        self.config = self._load_config(config_file)
        self.pool = None
        self._init_connection_pool()

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载数据库配置"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载数据库配置: {config_file}")
            return config
        except Exception as e:
            logger.error(f"加载数据库配置失败: {e}")
            raise

    def _init_connection_pool(self):
        """初始化连接池"""
        try:
            db_config = self.config["database"]
            pool_config = db_config.get("pool", {})

            # SSL配置
            ssl_config = None
            if db_config.get("ssl", {}).get("enabled", False):
                ssl_config = {
                    "ssl": {
                        "verify_cert": db_config["ssl"].get("verify_cert", False),
                        "ca_cert": db_config["ssl"].get("ca_cert"),
                    }
                }

            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=pool_config.get("max_connections", 5),
                mincached=pool_config.get("min_connections", 1),
                maxcached=pool_config.get("max_connections", 5),
                maxshared=3,
                blocking=True,
                maxusage=None,
                setsession=[],
                ping=0,
                host=db_config["host"],
                port=db_config["port"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"],
                charset=db_config.get("charset", "utf8mb4"),
                cursorclass=DictCursor,
                autocommit=db_config.get("autocommit", False),
                **ssl_config if ssl_config else {},
            )

            logger.info("数据库连接池初始化成功")

        except Exception as e:
            logger.error(f"初始化数据库连接池失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器

        Yields:
            pymysql.Connection: 数据库连接对象
        """
        connection = None
        try:
            connection = self.pool.connection()
            self._configure_connection(connection)
            yield connection
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    logger.warning(f"关闭数据库连接时出错: {e}")

    def _configure_connection(self, connection):
        """配置数据库连接参数"""
        try:
            # 设置会话变量
            session_vars = (
                self.config["database"]
                .get("performance", {})
                .get("session_variables", {})
            )
            if session_vars:
                for var_name, var_value in session_vars.items():
                    connection.cursor().execute(
                        f"SET SESSION {var_name} = %s", (var_value,)
                    )
                connection.commit()

            logger.debug("数据库连接配置完成")

        except Exception as e:
            logger.warning(f"配置数据库连接参数失败: {e}")

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            bool: 连接是否成功
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    logger.info("数据库连接测试成功")
                    return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def execute_query(self, sql: str, params: tuple = None) -> list:
        """
        执行查询语句

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            list: 查询结果
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchall()
                    logger.debug(f"执行查询成功: {sql[:100]}...")
                    return result
        except Exception as e:
            logger.error(f"执行查询失败: {sql[:100]}... - {e}")
            raise

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新语句

        Args:
            sql: SQL更新语句
            params: 更新参数

        Returns:
            int: 影响的行数
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    affected_rows = cursor.execute(sql, params)
                    conn.commit()
                    logger.debug(
                        f"执行更新成功: {sql[:100]}... - 影响行数: {affected_rows}"
                    )
                    return affected_rows
        except Exception as e:
            logger.error(f"执行更新失败: {sql[:100]}... - {e}")
            raise

    def execute_batch(self, sql: str, params_list: list) -> int:
        """
        批量执行SQL语句

        Args:
            sql: SQL语句模板
            params_list: 参数列表

        Returns:
            int: 总影响行数
        """
        total_affected = 0
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for params in params_list:
                        affected_rows = cursor.execute(sql, params)
                        total_affected += affected_rows
                    conn.commit()
                    logger.debug(
                        f"批量执行成功: {sql[:100]}... - 总影响行数: {total_affected}"
                    )
                    return total_affected
        except Exception as e:
            logger.error(f"批量执行失败: {sql[:100]}... - {e}")
            raise

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息

        Args:
            table_name: 表名

        Returns:
            Dict: 表信息
        """
        try:
            sql = """
                SELECT
                    TABLE_NAME,
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    CREATE_TIME,
                    UPDATE_TIME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            result = self.execute_query(
                sql, (self.config["database"]["database"], table_name)
            )
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"获取表信息失败: {table_name} - {e}")
            return {}

    def get_table_columns(self, table_name: str) -> list:
        """
        获取表的列信息

        Args:
            table_name: 表名

        Returns:
            list: 列信息列表
        """
        try:
            sql = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COLUMN_COMMENT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            return self.execute_query(
                sql, (self.config["database"]["database"], table_name)
            )
        except Exception as e:
            logger.error(f"获取表列信息失败: {table_name} - {e}")
            return []

    def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            logger.info("数据库连接池已关闭")


class DatabaseMonitor:
    """数据库监控器"""

    def __init__(self, connector: DatabaseConnector):
        self.connector = connector

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取数据库性能统计"""
        try:
            stats = {}

            # 获取连接数
            conn_sql = "SHOW STATUS LIKE 'Threads_connected'"
            conn_result = self.connector.execute_query(conn_sql)
            stats["connections"] = int(conn_result[0]["Value"]) if conn_result else 0

            # 获取慢查询数
            slow_sql = "SHOW STATUS LIKE 'Slow_queries'"
            slow_result = self.connector.execute_query(slow_sql)
            stats["slow_queries"] = int(slow_result[0]["Value"]) if slow_result else 0

            # 获取查询数
            query_sql = "SHOW STATUS LIKE 'Questions'"
            query_result = self.connector.execute_query(query_sql)
            stats["total_queries"] = (
                int(query_result[0]["Value"]) if query_result else 0
            )

            # 获取InnoDB状态
            innodb_sql = "SHOW ENGINE INNODB STATUS"
            innodb_result = self.connector.execute_query(innodb_sql)
            if innodb_result:
                stats["innodb_status"] = innodb_result[0]["Status"]

            return stats

        except Exception as e:
            logger.error(f"获取数据库性能统计失败: {e}")
            return {}

    def check_table_size(self, table_name: str) -> Dict[str, Any]:
        """检查表大小"""
        try:
            sql = """
                SELECT
                    TABLE_NAME,
                    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size_MB',
                    TABLE_ROWS
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            result = self.connector.execute_query(
                sql, (self.connector.config["database"]["database"], table_name)
            )
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"检查表大小失败: {table_name} - {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    import logging

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试连接
    connector = DatabaseConnector("config/database.yaml")

    if connector.test_connection():
        print("数据库连接测试成功")

        # 测试查询
        result = connector.execute_query("SELECT VERSION()")
        print(f"MySQL版本: {result[0]['VERSION()']}")

        # 测试监控
        monitor = DatabaseMonitor(connector)
        stats = monitor.get_performance_stats()
        print(f"性能统计: {stats}")

    connector.close()
