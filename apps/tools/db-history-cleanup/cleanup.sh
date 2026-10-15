#!/bin/bash
# -*- coding: utf-8 -*-
# 数据库历史数据清理工具执行脚本
# 提供便捷的命令行接口

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装或不在PATH中"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
}

# 检查依赖
check_dependencies() {
    log_info "检查Python依赖..."

    if ! python3 -c "import pymysql, yaml, tqdm" 2>/dev/null; then
        log_warn "缺少必要的Python依赖，正在安装..."
        pip3 install -r requirements.txt
    fi

    log_info "依赖检查完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."

    if [ ! -f "config/database.yaml" ]; then
        log_error "数据库配置文件不存在: config/database.yaml"
        log_info "请复制 config/database.yaml.example 并修改配置"
        exit 1
    fi

    if [ ! -f "config/cleanup-rules.yaml" ]; then
        log_error "清理规则配置文件不存在: config/cleanup-rules.yaml"
        exit 1
    fi

    log_info "配置文件检查完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."

    mkdir -p logs backups
    log_info "目录创建完成"
}

# 显示帮助信息
show_help() {
    echo "数据库历史数据清理工具 (安全版本)"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  analyze             执行数据分析"
    echo "  dry-run             试运行清理（不实际删除数据）"
    echo "  execute             执行实际清理（使用ID分页安全删除）"
    echo "  verify              验证清理结果"
    echo "  preview             获取清理预览信息"
    echo "  --table TABLE       指定表名"
    echo "  --output FILE       分析报告输出文件"
    echo "  --verbose           详细输出"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "安全特性:"
    echo "  - 基于ID字段清理，避免日期字段无默认值的问题"
    echo "  - 使用ID分页删除，避免重复删除或遗漏"
    echo "  - 自动验证表结构（主键、索引等）"
    echo "  - 安全检查和外键约束检查"
    echo "  - 详细的执行监控和日志"
    echo ""
    echo "示例:"
    echo "  $0 analyze                    # 分析数据"
    echo "  $0 dry-run                    # 试运行"
    echo "  $0 dry-run --table user_logs  # 试运行指定表"
    echo "  $0 execute                    # 执行清理"
    echo "  $0 verify                     # 验证结果"
    echo ""
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi

    # 环境检查
    check_python
    check_dependencies
    check_config
    create_directories

    # 构建Python命令
    PYTHON_CMD="python3 scripts/cleanup_manager.py"

    # 解析参数
    while [ $# -gt 0 ]; do
        case $1 in
            analyze)
                log_info "执行数据分析..."
                $PYTHON_CMD --analyze "${@:2}"
                break
                ;;
            dry-run)
                log_info "执行试运行..."
                $PYTHON_CMD --dry-run "${@:2}"
                break
                ;;
            execute)
                log_warn "准备执行实际清理操作..."
                log_warn "这将永久删除数据，请确保已备份重要数据！"
                read -p "确认继续？(yes/no): " confirm
                if [ "$confirm" = "yes" ]; then
                    log_info "执行实际清理..."
                    $PYTHON_CMD --execute "${@:2}"
                else
                    log_info "操作已取消"
                fi
                break
                ;;
            verify)
                log_info "验证清理结果..."
                $PYTHON_CMD --verify "${@:2}"
                break
                ;;
            preview)
                log_info "获取清理预览信息..."
                $PYTHON_CMD --preview "${@:2}"
                break
                ;;
            --table)
                PYTHON_CMD="$PYTHON_CMD --table $2"
                shift 2
                ;;
            --output)
                PYTHON_CMD="$PYTHON_CMD --output $2"
                shift 2
                ;;
            --verbose)
                PYTHON_CMD="$PYTHON_CMD --verbose"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 错误处理
trap 'log_error "脚本执行失败，退出码: $?"' ERR

# 执行主函数
main "$@"
