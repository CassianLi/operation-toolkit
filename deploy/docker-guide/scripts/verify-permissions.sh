#!/bin/bash

# Docker Compose 通用权限验证脚本
# 用于验证任何服务部署时的目录权限是否正确

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量 - 通过参数或环境变量设置
SERVICE_NAME="${1:-mysql}"
DOCKER_APPS_DIR="${DOCKER_APPS_DIR:-/opt/docker-apps}"
SERVICE_DIR="${DOCKER_APPS_DIR}/${SERVICE_NAME}"

# 目录列表 - 通用目录结构
DIRECTORIES=(
    "data"
    "logs"
    "config"
    "backups"
    "tmp"
)

# 验证结果统计
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 验证函数
check_result() {
    local test_name="$1"
    local result="$2"
    local expected="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ "$result" == "$expected" ]]; then
        log_success "✓ $test_name: $result"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "✗ $test_name: $result (期望: $expected)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# 检查目录是否存在
check_directory_exists() {
    local dir_path="$1"
    local dir_name="$2"

    if [[ -d "$dir_path" ]]; then
        check_result "$dir_name 目录存在" "存在" "存在"
    else
        check_result "$dir_name 目录存在" "不存在" "存在"
    fi
}

# 检查目录权限
check_directory_permission() {
    local dir_path="$1"
    local dir_name="$2"
    local expected_perm="$3"

    if [[ -d "$dir_path" ]]; then
        local actual_perm=$(stat -c "%a" "$dir_path")
        check_result "$dir_name 权限" "$actual_perm" "$expected_perm"
    else
        log_error "✗ $dir_name 权限: 目录不存在"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    fi
}

# 检查目录所有权
check_directory_ownership() {
    local dir_path="$1"
    local dir_name="$2"
    local expected_owner="$3"
    local expected_group="$4"

    if [[ -d "$dir_path" ]]; then
        local actual_owner=$(stat -c "%U" "$dir_path")
        local actual_group=$(stat -c "%G" "$dir_path")

        if [[ "$actual_owner" == "$expected_owner" && "$actual_group" == "$expected_group" ]]; then
            check_result "$dir_name 所有权" "$actual_owner:$actual_group" "$expected_owner:$expected_group"
        else
            log_error "✗ $dir_name 所有权: $actual_owner:$actual_group (期望: $expected_owner:$expected_group)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        fi
    else
        log_error "✗ $dir_name 所有权: 目录不存在"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    fi
}

# 检查用户组
check_user_group() {
    local current_group=$(id -gn)
    if groups | grep -q "\b$current_group\b"; then
        check_result "当前用户在 $current_group 组中" "是" "是"
    else
        check_result "当前用户在 $current_group 组中" "否" "是"
    fi
}

# 检查 Docker 服务状态
check_docker_service() {
    if systemctl is-active --quiet docker; then
        check_result "Docker 服务状态" "运行中" "运行中"
    else
        check_result "Docker 服务状态" "未运行" "运行中"
    fi
}

# 检查 Docker Compose 文件
check_compose_file() {
    local compose_file="${SERVICE_DIR}/docker-compose.yml"

    if [[ -f "$compose_file" ]]; then
        check_result "Docker Compose 文件存在" "存在" "存在"

        # 检查文件权限
        local file_perm=$(stat -c "%a" "$compose_file")
        check_result "Docker Compose 文件权限" "$file_perm" "644"

        # 检查文件内容
        if grep -q "user:" "$compose_file"; then
            check_result "Docker Compose 用户配置" "已配置" "已配置"
        else
            check_result "Docker Compose 用户配置" "未配置" "已配置"
        fi
    else
        check_result "Docker Compose 文件存在" "不存在" "存在"
    fi
}

# 检查容器状态
check_container_status() {
    if command -v docker >/dev/null 2>&1; then
        local container_name="${SERVICE_NAME}-server"
        local container_status=$(docker ps --filter "name=$container_name" --format "{{.Status}}" 2>/dev/null || echo "未运行")

        if [[ "$container_status" == *"Up"* ]]; then
            check_result "$SERVICE_NAME 容器状态" "运行中" "运行中"
        else
            check_result "$SERVICE_NAME 容器状态" "未运行" "运行中"
        fi
    else
        log_warning "Docker 命令不可用，跳过容器状态检查"
    fi
}

# 检查挂载点
check_mount_points() {
    if command -v docker >/dev/null 2>&1; then
        local container_name="${SERVICE_NAME}-server"
        local mount_info=$(docker inspect "$container_name" --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' 2>/dev/null || echo "")

        if [[ -n "$mount_info" ]]; then
            check_result "容器挂载点" "已配置" "已配置"
            log_info "挂载点信息: $mount_info"
        else
            check_result "容器挂载点" "未配置" "已配置"
        fi
    else
        log_warning "Docker 命令不可用，跳过挂载点检查"
    fi
}

# 检查日志文件
check_log_files() {
    local log_dir="${SERVICE_DIR}/logs"

    if [[ -d "$log_dir" ]]; then
        local log_files=$(find "$log_dir" -name "*.log" 2>/dev/null | wc -l)

        if [[ $log_files -gt 0 ]]; then
            check_result "日志文件数量" "$log_files" ">0"
        else
            check_result "日志文件数量" "0" ">0"
        fi
    else
        log_warning "日志目录不存在: $log_dir"
    fi
}

# 生成验证报告
generate_report() {
    echo
    log_info "=== 验证报告 ==="
    echo
    log_info "总检查项: $TOTAL_CHECKS"
    log_success "通过: $PASSED_CHECKS"
    log_error "失败: $FAILED_CHECKS"
    echo

    local success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    log_info "成功率: ${success_rate}%"
    echo

    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "所有检查项都通过了！"
        return 0
    else
        log_error "有 $FAILED_CHECKS 个检查项失败，请检查上述错误信息"
        return 1
    fi
}

# 显示详细权限信息
show_detailed_permissions() {
    echo
    log_info "=== 详细权限信息 ==="
    echo

    if [[ -d "$DOCKER_APPS_DIR" ]]; then
        log_info "主目录权限:"
        ls -la "$DOCKER_APPS_DIR"
        echo
    fi

    if [[ -d "$SERVICE_DIR" ]]; then
        log_info "服务目录权限:"
        ls -la "$SERVICE_DIR"
        echo

        for dir in "${DIRECTORIES[@]}"; do
            local dir_path="${SERVICE_DIR}/${dir}"
            if [[ -d "$dir_path" ]]; then
                log_info "$dir 目录权限:"
                ls -la "$dir_path"
                echo
            fi
        done
    fi
}

# 主函数
main() {
    log_info "开始验证 Docker Compose 目录权限..."
    echo

    # 基本检查
    check_user_group
    check_docker_service

    # 目录检查
    check_directory_exists "$DOCKER_APPS_DIR" "主目录"
    check_directory_exists "$SERVICE_DIR" "服务目录"

    # 权限检查
    if [[ -d "$DOCKER_APPS_DIR" ]]; then
        check_directory_permission "$DOCKER_APPS_DIR" "主目录" "755"
        check_directory_ownership "$DOCKER_APPS_DIR" "主目录" "$USER" "$(id -gn)"
    fi

    if [[ -d "$SERVICE_DIR" ]]; then
        check_directory_permission "$SERVICE_DIR" "服务目录" "755"
        check_directory_ownership "$SERVICE_DIR" "服务目录" "$USER" "$(id -gn)"

        # 子目录检查
        for dir in "${DIRECTORIES[@]}"; do
            local dir_path="${SERVICE_DIR}/${dir}"
            check_directory_exists "$dir_path" "$dir 目录"
            check_directory_permission "$dir_path" "$dir 目录" "755"
            check_directory_ownership "$dir_path" "$dir 目录" "$USER" "$(id -gn)"
        done
    fi

    # 文件检查
    check_compose_file

    # 容器检查
    check_container_status
    check_mount_points

    # 日志检查
    check_log_files

    # 生成报告
    generate_report

    # 显示详细权限信息
    show_detailed_permissions

    echo
    log_info "验证完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
