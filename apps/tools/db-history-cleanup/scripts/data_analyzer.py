#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析工具模块
提供基于ID的数据量分析、清理影响评估等功能
"""

import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import sys
import os


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


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, db_connector: DatabaseConnector, config_file: str):
        """
        初始化数据分析器

        Args:
            db_connector: 数据库连接器
            config_file: 清理规则配置文件
        """
        self.db_connector = db_connector
        self.monitor = DatabaseMonitor(db_connector)
        self.config = self._load_config(config_file)

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

    def analyze_table_data(self, table_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个表的数据

        Args:
            table_config: 表配置

        Returns:
            Dict: 分析结果
        """
        table_name = table_config["name"]
        max_id = table_config["max_id"]

        logger.info(f"开始分析表: {table_name}")

        try:
            # 获取表基本信息
            table_info = self.db_connector.get_table_info(table_name)
            if not table_info:
                logger.warning(f"表 {table_name} 不存在或无法访问")
                return {}

            # 分析数据分布
            data_distribution = self._analyze_data_distribution(
                table_name, max_id
            )

            # 计算清理影响
            cleanup_impact = self._calculate_cleanup_impact(
                table_name, max_id, data_distribution
            )

            # 生成分析报告
            analysis_result = {
                "table_name": table_name,
                "max_id": max_id,
                "table_info": table_info,
                "data_distribution": data_distribution,
                "cleanup_impact": cleanup_impact,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            logger.info(f"表 {table_name} 分析完成")
            return analysis_result

        except Exception as e:
            logger.error(f"分析表 {table_name} 失败: {e}")
            return {"error": str(e)}

    def _analyze_data_distribution(self, table_name: str, max_id: int) -> Dict[str, Any]:
        """分析数据分布"""
        try:
            # 获取总记录数
            total_count_sql = f"SELECT COUNT(*) as count FROM {table_name}"
            total_result = self.db_connector.execute_query(total_count_sql)
            total_records = total_result[0]["count"] if total_result else 0

            # 获取需要清理的记录数
            cleanup_count_sql = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE id < %s
            """
            cleanup_result = self.db_connector.execute_query(cleanup_count_sql, (max_id,))
            cleanup_records = cleanup_result[0]["count"] if cleanup_result else 0

            # 获取ID范围
            id_range_sql = f"""
                SELECT 
                    MIN(id) as min_id,
                    MAX(id) as max_id,
                    COUNT(*) as count
                FROM {table_name}
            """
            id_range_result = self.db_connector.execute_query(id_range_sql)
            id_range = id_range_result[0] if id_range_result else {}

            # 计算清理比例
            cleanup_ratio = (cleanup_records / total_records * 100) if total_records > 0 else 0

            # 获取表大小信息
            table_size = self.monitor.check_table_size(table_name)

            return {
                "total_records": total_records,
                "cleanup_records": cleanup_records,
                "cleanup_ratio": round(cleanup_ratio, 2),
                "id_range": {
                    "min_id": id_range.get("min_id"),
                    "max_id": id_range.get("max_id"),
                    "current_max_id": max_id,
                },
                "table_size_mb": table_size.get("Size_MB", 0),
                "index_size_mb": table_size.get("Index_Size_MB", 0),
            }

        except Exception as e:
            logger.error(f"分析数据分布失败: {e}")
            return {"error": str(e)}

    def _calculate_cleanup_impact(self, table_name: str, max_id: int, data_distribution: Dict[str, Any]) -> Dict[str, Any]:
        """计算清理影响"""
        try:
            total_records = data_distribution.get("total_records", 0)
            cleanup_records = data_distribution.get("cleanup_records", 0)
            table_size_mb = data_distribution.get("table_size_mb", 0)

            # 估算清理后的表大小
            if total_records > 0:
                avg_record_size_mb = table_size_mb / total_records
                estimated_size_after_mb = (total_records - cleanup_records) * avg_record_size_mb
                estimated_space_saved_mb = table_size_mb - estimated_size_after_mb
            else:
                estimated_size_after_mb = 0
                estimated_space_saved_mb = 0

            # 估算清理时间（基于批处理大小）
            batch_size = self.config.get("global", {}).get("batch_size", 1000)
            estimated_batches = (cleanup_records + batch_size - 1) // batch_size
            estimated_time_seconds = estimated_batches * 0.1  # 假设每批次0.1秒

            return {
                "estimated_space_saved_mb": round(estimated_space_saved_mb, 2),
                "estimated_size_after_mb": round(estimated_size_after_mb, 2),
                "estimated_batches": estimated_batches,
                "estimated_time_seconds": round(estimated_time_seconds, 2),
                "estimated_time_minutes": round(estimated_time_seconds / 60, 2),
                "cleanup_efficiency": round(cleanup_records / estimated_batches, 2) if estimated_batches > 0 else 0,
            }

        except Exception as e:
            logger.error(f"计算清理影响失败: {e}")
            return {"error": str(e)}

    def analyze_all_tables(self) -> Dict[str, Any]:
        """
        分析所有配置的表

        Returns:
            Dict: 分析结果汇总
        """
        logger.info("开始分析所有表")

        analysis_summary = {
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables_analyzed": 0,
            "total_records_to_clean": 0,
            "total_space_to_save_mb": 0,
            "estimated_total_time_minutes": 0,
            "table_details": {},
            "errors": [],
        }

        try:
            tables = self.config.get("tables", [])
            enabled_tables = [t for t in tables if t.get("enabled", True)]

            for table_config in enabled_tables:
                table_name = table_config["name"]
                logger.info(f"分析表: {table_name}")

                try:
                    analysis_result = self.analyze_table_data(table_config)
                    
                    if "error" not in analysis_result:
                        analysis_summary["tables_analyzed"] += 1
                        analysis_summary["table_details"][table_name] = analysis_result

                        # 累计统计
                        cleanup_impact = analysis_result.get("cleanup_impact", {})
                        data_distribution = analysis_result.get("data_distribution", {})
                        
                        analysis_summary["total_records_to_clean"] += data_distribution.get("cleanup_records", 0)
                        analysis_summary["total_space_to_save_mb"] += cleanup_impact.get("estimated_space_saved_mb", 0)
                        analysis_summary["estimated_total_time_minutes"] += cleanup_impact.get("estimated_time_minutes", 0)
                    else:
                        analysis_summary["errors"].append(f"表 {table_name}: {analysis_result['error']}")

                except Exception as e:
                    error_msg = f"分析表 {table_name} 失败: {e}"
                    logger.error(error_msg)
                    analysis_summary["errors"].append(error_msg)

            # 格式化汇总信息
            analysis_summary["total_space_to_save_mb"] = round(analysis_summary["total_space_to_save_mb"], 2)
            analysis_summary["estimated_total_time_minutes"] = round(analysis_summary["estimated_total_time_minutes"], 2)

            logger.info("所有表分析完成")
            return analysis_summary

        except Exception as e:
            logger.error(f"分析所有表失败: {e}")
            analysis_summary["errors"].append(str(e))
            return analysis_summary

    def get_id_recommendations(self, table_name: str = None) -> Dict[str, Any]:
        """
        获取ID配置建议

        Args:
            table_name: 指定表名，如果为None则分析所有表

        Returns:
            Dict: ID配置建议
        """
        logger.info("开始获取ID配置建议")

        recommendations = {
            "recommendation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables_analyzed": 0,
            "recommendations": {},
            "errors": [],
        }

        try:
            tables = self.config.get("tables", [])
            if table_name:
                tables = [t for t in tables if t["name"] == table_name]

            for table_config in tables:
                table_name = table_config["name"]
                current_max_id = table_config.get("max_id", 0)

                logger.info(f"分析表 {table_name} 的ID配置")

                try:
                    # 获取当前ID分布
                    id_distribution_sql = f"""
                        SELECT 
                            MIN(id) as min_id,
                            MAX(id) as max_id,
                            COUNT(*) as total_count,
                            AVG(id) as avg_id
                        FROM {table_name}
                    """
                    result = self.db_connector.execute_query(id_distribution_sql)
                    
                    if result:
                        id_info = result[0]
                        current_max_table_id = id_info.get("max_id", 0)
                        total_count = id_info.get("total_count", 0)
                        avg_id = id_info.get("avg_id", 0)

                        # 计算建议的max_id（保留最近的数据）
                        # 这里可以根据业务需求调整保留策略
                        if current_max_table_id > 0:
                            # 建议保留最后20%的数据
                            suggested_max_id = int(current_max_table_id * 0.8)
                            
                            # 确保建议的ID不超过当前配置
                            if suggested_max_id > current_max_id:
                                suggested_max_id = current_max_id

                            recommendations["tables_analyzed"] += 1
                            recommendations["recommendations"][table_name] = {
                                "current_max_id": current_max_id,
                                "table_max_id": current_max_table_id,
                                "total_records": total_count,
                                "avg_id": round(avg_id, 2) if avg_id else 0,
                                "suggested_max_id": suggested_max_id,
                                "records_to_clean_with_suggestion": 0,
                                "current_records_to_clean": 0,
                            }

                            # 计算使用建议ID时的清理记录数
                            if suggested_max_id > 0:
                                count_sql = f"""
                                    SELECT COUNT(*) as count
                                    FROM {table_name}
                                    WHERE id < %s
                                """
                                count_result = self.db_connector.execute_query(count_sql, (suggested_max_id,))
                                records_to_clean = count_result[0]["count"] if count_result else 0
                                recommendations["recommendations"][table_name]["records_to_clean_with_suggestion"] = records_to_clean

                            # 计算当前配置的清理记录数
                            if current_max_id > 0:
                                count_sql = f"""
                                    SELECT COUNT(*) as count
                                    FROM {table_name}
                                    WHERE id < %s
                                """
                                count_result = self.db_connector.execute_query(count_sql, (current_max_id,))
                                records_to_clean = count_result[0]["count"] if count_result else 0
                                recommendations["recommendations"][table_name]["current_records_to_clean"] = records_to_clean

                    else:
                        recommendations["errors"].append(f"表 {table_name}: 无法获取ID分布信息")

                except Exception as e:
                    error_msg = f"分析表 {table_name} 的ID配置失败: {e}"
                    logger.error(error_msg)
                    recommendations["errors"].append(error_msg)

            logger.info("ID配置建议分析完成")
            return recommendations

        except Exception as e:
            logger.error(f"获取ID配置建议失败: {e}")
            recommendations["errors"].append(str(e))
            return recommendations

    def generate_analysis_report(self, output_file: str = None) -> str:
        """
        生成分析报告

        Args:
            output_file: 输出文件路径，如果为None则返回报告内容

        Returns:
            str: 报告内容或文件路径
        """
        logger.info("开始生成分析报告")

        try:
            # 获取所有表的分析结果
            analysis_summary = self.analyze_all_tables()
            id_recommendations = self.get_id_recommendations()

            # 生成报告内容
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("数据库清理分析报告")
            report_lines.append("=" * 80)
            report_lines.append(f"生成时间: {analysis_summary['analysis_time']}")
            report_lines.append("")

            # 汇总信息
            report_lines.append("汇总信息:")
            report_lines.append(f"  分析表数: {analysis_summary['tables_analyzed']}")
            report_lines.append(f"  总清理记录数: {analysis_summary['total_records_to_clean']:,}")
            report_lines.append(f"  预计节省空间: {analysis_summary['total_space_to_save_mb']:.2f}MB")
            report_lines.append(f"  预计总耗时: {analysis_summary['estimated_total_time_minutes']:.2f}分钟")
            report_lines.append("")

            # 详细分析
            report_lines.append("详细分析:")
            report_lines.append("-" * 40)
            
            for table_name, details in analysis_summary.get("table_details", {}).items():
                report_lines.append(f"表名: {table_name}")
                
                data_dist = details.get("data_distribution", {})
                cleanup_impact = details.get("cleanup_impact", {})
                
                report_lines.append(f"  总记录数: {data_dist.get('total_records', 0):,}")
                report_lines.append(f"  清理记录数: {data_dist.get('cleanup_records', 0):,}")
                report_lines.append(f"  清理比例: {data_dist.get('cleanup_ratio', 0):.2f}%")
                report_lines.append(f"  当前表大小: {data_dist.get('table_size_mb', 0):.2f}MB")
                report_lines.append(f"  预计节省空间: {cleanup_impact.get('estimated_space_saved_mb', 0):.2f}MB")
                report_lines.append(f"  预计耗时: {cleanup_impact.get('estimated_time_minutes', 0):.2f}分钟")
                report_lines.append("")

            # ID配置建议
            report_lines.append("ID配置建议:")
            report_lines.append("-" * 40)
            
            for table_name, rec in id_recommendations.get("recommendations", {}).items():
                report_lines.append(f"表名: {table_name}")
                report_lines.append(f"  当前配置max_id: {rec.get('current_max_id', 0):,}")
                report_lines.append(f"  表最大ID: {rec.get('table_max_id', 0):,}")
                report_lines.append(f"  建议max_id: {rec.get('suggested_max_id', 0):,}")
                report_lines.append(f"  当前配置清理记录数: {rec.get('current_records_to_clean', 0):,}")
                report_lines.append(f"  建议配置清理记录数: {rec.get('records_to_clean_with_suggestion', 0):,}")
                report_lines.append("")

            # 错误信息
            if analysis_summary.get("errors"):
                report_lines.append("错误信息:")
                report_lines.append("-" * 40)
                for error in analysis_summary["errors"]:
                    report_lines.append(f"  - {error}")
                report_lines.append("")

            report_lines.append("=" * 80)

            report_content = "\n".join(report_lines)

            # 输出到文件或返回内容
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report_content)
                logger.info(f"分析报告已保存到: {output_file}")
                return output_file
            else:
                return report_content

        except Exception as e:
            logger.error(f"生成分析报告失败: {e}")
            return f"生成分析报告失败: {e}"


if __name__ == "__main__":
    # 测试代码
    import logging

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试分析
    db_connector = DatabaseConnector("config/database.yaml")
    analyzer = DataAnalyzer(db_connector, "config/cleanup-rules.yaml")

    results = analyzer.analyze_all_tables()
    report = analyzer.generate_analysis_report(output_file="logs/analysis_report.txt")

    print(report)

    db_connector.close()
