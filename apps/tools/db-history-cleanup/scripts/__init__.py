# -*- coding: utf-8 -*-
"""
数据库历史数据清理工具包
"""

__version__ = "1.0.0"
__author__ = "Operation Toolkit"
__description__ = "生产数据库历史数据清理工具"


# 动态导入模块
def _import_modules():
    """动态导入所有模块"""
    try:
        from .db_connector import DatabaseConnector, DatabaseMonitor
        from .data_analyzer import DataAnalyzer
        from .cleanup_executor import CleanupExecutor
        from .cleanup_manager import CleanupManager

        return (
            DatabaseConnector,
            DatabaseMonitor,
            DataAnalyzer,
            CleanupExecutor,
            CleanupManager,
        )
    except ImportError:
        # 如果相对导入失败，尝试绝对导入
        try:
            from scripts.db_connector import DatabaseConnector, DatabaseMonitor
            from scripts.data_analyzer import DataAnalyzer
            from scripts.cleanup_executor import CleanupExecutor
            from scripts.cleanup_manager import CleanupManager

            return (
                DatabaseConnector,
                DatabaseMonitor,
                DataAnalyzer,
                CleanupExecutor,
                CleanupManager,
            )
        except ImportError:
            # 如果都失败，返回None
            return None, None, None, None, None


# 导入模块
DatabaseConnector, DatabaseMonitor, DataAnalyzer, CleanupExecutor, CleanupManager = (
    _import_modules()
)

__all__ = [
    "DatabaseConnector",
    "DatabaseMonitor",
    "DataAnalyzer",
    "CleanupExecutor",
    "CleanupManager",
]
