#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库历史数据清理管理器
主控制脚本，协调各个模块完成清理任务
"""

import argparse
import logging
import logging.config
import os
import sys
from typing import Any, Dict


# 动态导入模块，支持不同的运行方式
def import_modules():
    """动态导入模块，支持包导入和直接运行"""
    try:
        # 方式1：作为包导入（相对导入）
        from .safe_cleanup_executor import SafeCleanupExecutor
        from .data_analyzer import DataAnalyzer
        from .db_connector import DatabaseConnector
    except ImportError:
        try:
            # 方式2：绝对导入（作为包）
            from scripts.safe_cleanup_executor import SafeCleanupExecutor
            from scripts.data_analyzer import DataAnalyzer
            from scripts.db_connector import DatabaseConnector
        except ImportError:
            # 方式3：直接导入（当前目录）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from safe_cleanup_executor import SafeCleanupExecutor
            from data_analyzer import DataAnalyzer
            from db_connector import DatabaseConnector

    return SafeCleanupExecutor, DataAnalyzer, DatabaseConnector


# 导入模块
SafeCleanupExecutor, DataAnalyzer, DatabaseConnector = import_modules()


# 配置日志
def setup_logging():
    """设置日志配置"""
    try:
        logging.config.fileConfig("config/logging.yaml")
    except Exception as e:
        # 如果配置文件不存在，使用基本配置
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("logs/cleanup.log", encoding="utf-8"),
            ],
        )
        logging.warning(f"使用基本日志配置: {e}")


class CleanupManager:
    """清理管理器"""

    def __init__(self, db_config_file: str, rules_config_file: str):
        """
        初始化清理管理器

        Args:
            db_config_file: 数据库配置文件路径
            rules_config_file: 清理规则配置文件路径
        """
        self.db_config_file = db_config_file
        self.rules_config_file = rules_config_file

        # 初始化组件
        self.db_connector = None
        self.analyzer = None
        self.executor = None

        # 创建必要目录
        self._create_directories()

    def _create_directories(self):
        """创建必要的目录"""
        directories = ["logs", "backups"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(f"创建目录: {directory}")

    def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            logging.info("初始化清理管理器...")

            # 初始化数据库连接器
            self.db_connector = DatabaseConnector(self.db_config_file)

            # 测试数据库连接
            if not self.db_connector.test_connection():
                logging.error("数据库连接测试失败")
                return False

            # 初始化分析器
            self.analyzer = DataAnalyzer(self.db_connector, self.rules_config_file)

            # 初始化安全执行器
            self.executor = SafeCleanupExecutor(
                self.db_connector, self.rules_config_file
            )

            logging.info("清理管理器初始化成功")
            return True

        except Exception as e:
            logging.error(f"初始化清理管理器失败: {e}")
            return False

    def analyze_data(self, output_file: str = None) -> Dict[str, Any]:
        """
        分析数据

        Args:
            output_file: 分析报告输出文件

        Returns:
            Dict: 分析结果
        """
        logging.info("开始数据分析...")

        try:
            # 执行数据分析
            analysis_results = self.analyzer.analyze_all_tables()

            # 生成报告
            if output_file:
                report = self.analyzer.generate_analysis_report(output_file)
            else:
                report = self.analyzer.generate_analysis_report()

            # 打印报告摘要
            self._print_analysis_summary(analysis_results)

            return analysis_results

        except Exception as e:
            logging.error(f"数据分析失败: {e}")
            raise

    def _print_analysis_summary(self, analysis_results: Dict[str, Any]):
        """打印分析摘要"""
        print("\n" + "=" * 60)
        print("数据分析摘要")
        print("=" * 60)
        print(f"分析时间: {analysis_results['analysis_time']}")
        print(f"分析表数: {analysis_results['tables_analyzed']}")
        print(f"待清理记录: {analysis_results['total_records_to_clean']:,}")
        print(f"预计节省空间: {analysis_results['total_space_to_save_mb']:.2f}MB")
        print(
            f"预估执行时间: {analysis_results['estimated_total_time_minutes']:.2f} 分钟"
        )

        if analysis_results.get("errors"):
            print(f"错误数量: {len(analysis_results['errors'])}")

        print("=" * 60)

    def execute_cleanup(
        self, dry_run: bool = True, table_name: str = None
    ) -> Dict[str, Any]:
        """
        执行清理操作

        Args:
            dry_run: 是否试运行
            table_name: 指定表名

        Returns:
            Dict: 执行结果
        """
        if dry_run:
            logging.info("开始试运行清理操作...")
        else:
            logging.info("开始执行实际清理操作...")

        try:
            # 执行安全清理
            results = self.executor.execute_safe_cleanup(
                dry_run=dry_run, table_name=table_name
            )

            # 打印执行摘要
            self._print_execution_summary(results)

            return results

        except Exception as e:
            logging.error(f"清理执行失败: {e}")
            raise

    def _print_execution_summary(self, results: Dict[str, Any]):
        """打印执行摘要"""
        if not results["end_time"]:
            return

        duration = (results["end_time"] - results["start_time"]).total_seconds()

        print("\n" + "=" * 60)
        print("清理执行摘要")
        print("=" * 60)
        print(f"执行时间: {duration:.2f} 秒")
        print(f"处理表数: {results['tables_processed']}")
        print(f"清理记录数: {results['total_records_cleaned']:,}")
        print(f"节省空间: {results['total_space_saved_mb']:.2f}MB")

        if results["errors"]:
            print(f"错误数量: {len(results['errors'])}")
            for error in results["errors"][:3]:  # 只显示前3个错误
                print(f"  - {error}")

        print("=" * 60)

    def verify_cleanup(self, table_name: str = None) -> Dict[str, Any]:
        """
        验证清理结果

        Args:
            table_name: 指定表名

        Returns:
            Dict: 验证结果
        """
        logging.info("开始验证清理结果...")

        try:
            verification_results = self.executor.verify_safe_cleanup(table_name)

            # 打印验证摘要
            self._print_verification_summary(verification_results)

            return verification_results

        except Exception as e:
            logging.error(f"验证清理结果失败: {e}")
            raise

    def _print_verification_summary(self, results: Dict[str, Any]):
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("清理验证摘要")
        print("=" * 60)
        print(f"验证时间: {results['verification_time']}")
        print(f"验证表数: {results['tables_verified']}")
        print(f"验证通过: {results['verification_passed']}")
        print(f"验证失败: {results['verification_failed']}")

        if results["verification_failed"] > 0:
            print("\n验证失败的表:")
            for table_name, detail in results["details"].items():
                if detail["status"] == "failed":
                    print(f"  - {table_name}: {detail['remaining_records']} 条剩余记录")

        print("=" * 60)

    def get_cleanup_preview(self, table_name: str = None) -> Dict[str, Any]:
        """获取清理预览信息"""
        logging.info("获取清理预览信息...")

        try:
            preview_results = self.executor.get_safe_cleanup_preview(table_name)

            # 打印预览摘要
            self._print_preview_summary(preview_results)

            return preview_results

        except Exception as e:
            logging.error(f"获取清理预览信息失败: {e}")
            raise

    def _print_preview_summary(self, results: Dict[str, Any]):
        """打印预览摘要"""
        print("\n" + "=" * 60)
        print("清理预览信息")
        print("=" * 60)
        print(f"预览时间: {results['preview_time']}")
        print(f"预览表数: {results['tables_previewed']}")
        print(f"总清理记录数: {results['total_records_to_clean']:,}")
        print(f"预计节省空间: {results['estimated_space_saved_mb']:.2f}MB")
        print(f"安全检查通过: {results['safety_checks_passed']}")
        print(f"安全检查失败: {results['safety_checks_failed']}")
        print("=" * 60)

    def cleanup(self):
        """清理资源"""
        if self.db_connector:
            self.db_connector.close()
            logging.info("数据库连接已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库历史数据清理工具")
    parser.add_argument(
        "--db-config", default="config/database.yaml", help="数据库配置文件路径"
    )
    parser.add_argument(
        "--rules-config",
        default="config/cleanup-rules.yaml",
        help="清理规则配置文件路径",
    )
    parser.add_argument("--analyze", action="store_true", help="执行数据分析")
    parser.add_argument("--dry-run", action="store_true", help="试运行模式")
    parser.add_argument("--execute", action="store_true", help="执行实际清理")
    parser.add_argument("--verify", action="store_true", help="验证清理结果")
    parser.add_argument("--preview", action="store_true", help="获取清理预览信息")
    parser.add_argument("--table", type=str, help="指定表名")
    parser.add_argument("--output", type=str, help="分析报告输出文件")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 初始化清理管理器
    manager = CleanupManager(args.db_config, args.rules_config)

    try:
        # 初始化
        if not manager.initialize():
            sys.exit(1)

        # 执行相应操作
        if args.analyze:
            manager.analyze_data(args.output)

        if args.dry_run:
            manager.execute_cleanup(dry_run=True, table_name=args.table)

        if args.execute:
            # 确认执行
            if not args.dry_run:
                confirm = input("确认执行实际清理操作？这将永久删除数据！(yes/no): ")
                if confirm.lower() != "yes":
                    print("操作已取消")
                    return

            manager.execute_cleanup(dry_run=False, table_name=args.table)

        if args.verify:
            manager.verify_cleanup(args.table)

        if args.preview:
            manager.get_cleanup_preview(args.table)

        # 如果没有指定任何操作，显示帮助
        if not any(
            [args.analyze, args.dry_run, args.execute, args.verify, args.preview]
        ):
            parser.print_help()

    except KeyboardInterrupt:
        logging.info("操作被用户中断")
    except Exception as e:
        logging.error(f"操作失败: {e}")
        sys.exit(1)
    finally:
        manager.cleanup()


if __name__ == "__main__":
    # 设置日志
    setup_logging()

    # 运行主函数
    main()
