#!/bin/bash

# Docker Compose 通用目录权限设置脚本
# 用于设置任何服务部署时的目录权限

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

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用 root 用户运行此脚本"
        exit 1
    fi
}

# 获取当前用户组信息
get_user_info() {
    log_info "获取当前用户信息..."
    local user_info=$(id)
    log_info "用户信息: $user_info"

    # 提取用户ID和组ID
    HOST_USER_ID=$(id -u)
    HOST_GROUP_ID=$(id -g)
    HOST_USER_NAME=$(id -un)
    HOST_GROUP_NAME=$(id -gn)

    log_info "用户ID: $HOST_USER_ID"
    log_info "组ID: $HOST_GROUP_ID"
    log_info "用户名: $HOST_USER_NAME"
    log_info "组名: $HOST_GROUP_NAME"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."

    # 创建主目录
    sudo mkdir -p "$DOCKER_APPS_DIR"
    sudo mkdir -p "$SERVICE_DIR"

    # 创建子目录
    for dir in "${DIRECTORIES[@]}"; do
        sudo mkdir -p "${SERVICE_DIR}/${dir}"
        log_success "创建目录: ${SERVICE_DIR}/${dir}"
    done
}

# 设置目录权限
set_permissions() {
    log_info "设置目录权限..."

    # 设置主目录权限
    sudo chown -R "$HOST_USER_NAME:$HOST_GROUP_NAME" "$DOCKER_APPS_DIR"
    sudo chmod -R 755 "$DOCKER_APPS_DIR"
    log_success "设置主目录权限: $DOCKER_APPS_DIR"

    # 设置服务目录权限
    sudo chown -R "$HOST_USER_NAME:$HOST_GROUP_NAME" "$SERVICE_DIR"
    sudo chmod -R 755 "$SERVICE_DIR"
    log_success "设置服务目录权限: $SERVICE_DIR"

    # 设置子目录权限
    for dir in "${DIRECTORIES[@]}"; do
        local dir_path="${SERVICE_DIR}/${dir}"
        sudo chown -R "$HOST_USER_NAME:$HOST_GROUP_NAME" "$dir_path"
        sudo chmod -R 755 "$dir_path"
        log_success "设置目录权限: $dir_path"
    done
}

# 创建必要的文件
create_files() {
    log_info "创建必要的文件..."

    # 创建日志目录下的子目录
    sudo mkdir -p "${SERVICE_DIR}/logs/service"
    sudo chown -R "$HOST_USER_NAME:$HOST_GROUP_NAME" "${SERVICE_DIR}/logs"
    sudo chmod -R 755 "${SERVICE_DIR}/logs"

    # 创建备份目录下的子目录
    sudo mkdir -p "${SERVICE_DIR}/backups/daily"
    sudo mkdir -p "${SERVICE_DIR}/backups/weekly"
    sudo mkdir -p "${SERVICE_DIR}/backups/monthly"
    sudo chown -R "$HOST_USER_NAME:$HOST_GROUP_NAME" "${SERVICE_DIR}/backups"
    sudo chmod -R 755 "${SERVICE_DIR}/backups"

    log_success "创建必要的子目录"
}

# 验证权限设置
verify_permissions() {
    log_info "验证权限设置..."

    # 检查主目录权限
    local main_perm=$(stat -c "%a" "$DOCKER_APPS_DIR")
    if [[ "$main_perm" == "755" ]]; then
        log_success "主目录权限正确: $main_perm"
    else
        log_error "主目录权限错误: $main_perm (期望: 755)"
    fi

    # 检查服务目录权限
    local service_perm=$(stat -c "%a" "$SERVICE_DIR")
    if [[ "$service_perm" == "755" ]]; then
        log_success "服务目录权限正确: $service_perm"
    else
        log_error "服务目录权限错误: $service_perm (期望: 755)"
    fi

    # 检查子目录权限
    for dir in "${DIRECTORIES[@]}"; do
        local dir_path="${SERVICE_DIR}/${dir}"
        local perm=$(stat -c "%a" "$dir_path")
        if [[ "$perm" == "755" ]]; then
            log_success "目录权限正确: $dir_path ($perm)"
        else
            log_error "目录权限错误: $dir_path ($perm, 期望: 755)"
        fi
    done
}

# 显示目录结构
show_structure() {
    log_info "目录结构:"
    tree "$DOCKER_APPS_DIR" 2>/dev/null || ls -la "$DOCKER_APPS_DIR"
    echo
    log_info "服务目录结构:"
    tree "$SERVICE_DIR" 2>/dev/null || ls -la "$SERVICE_DIR"
}

# 显示权限信息
show_permissions() {
    log_info "权限信息:"
    echo
    log_info "主目录权限:"
    ls -la "$DOCKER_APPS_DIR"
    echo
    log_info "服务目录权限:"
    ls -la "$SERVICE_DIR"
    echo
    log_info "子目录权限:"
    for dir in "${DIRECTORIES[@]}"; do
        echo "=== ${SERVICE_DIR}/${dir} ==="
        ls -la "${SERVICE_DIR}/${dir}"
    done
}

# 生成环境变量配置
generate_env_config() {
    log_info "生成环境变量配置..."

    local env_file="${SERVICE_DIR}/.env"
    cat > "$env_file" << EOF
# 宿主机用户信息配置
HOST_USER_ID=${HOST_USER_ID}
HOST_GROUP_ID=${HOST_GROUP_ID}
HOST_USER_NAME=${HOST_USER_NAME}
HOST_GROUP_NAME=${HOST_GROUP_NAME}

# 服务配置
SERVICE_NAME=${SERVICE_NAME}
SERVICE_DIR=${SERVICE_DIR}

# 系统配置
TZ=Asia/Shanghai
EOF

    log_success "生成环境变量配置文件: $env_file"
}

# 主函数
main() {
    log_info "开始设置 Docker Compose 目录权限..."
    echo

    # 检查环境
    check_root
    get_user_info

    # 执行设置
    create_directories
    set_permissions
    create_files
    verify_permissions
    generate_env_config

    echo
    log_success "目录权限设置完成!"
    echo

    # 显示结果
    show_structure
    echo
    show_permissions

    echo
    log_info "下一步操作:"
    log_info "1. 复制 docker-compose.yml 到 $SERVICE_DIR"
    log_info "2. 复制配置文件到 $SERVICE_DIR/config"
    log_info "3. 编辑 $SERVICE_DIR/.env 文件，设置服务特定配置"
    log_info "4. 运行: docker compose up -d"
    echo
    log_info "用户映射信息:"
    log_info "- 宿主机用户 ID: $HOST_USER_ID"
    log_info "- 宿主机组 ID: $HOST_GROUP_ID"
    log_info "- 宿主机用户名: $HOST_USER_NAME"
    log_info "- 宿主机组名: $HOST_GROUP_NAME"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
