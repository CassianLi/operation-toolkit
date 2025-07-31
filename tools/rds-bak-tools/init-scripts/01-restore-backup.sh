#!/bin/bash
set -e

# 恢复目录必须有足够空间且权限为 mysql:mysql（通常为 999:999），可用如下命令：
#   sudo mkdir -p /data/databases/mysql/restore
#   sudo chown -R 999:999 /data/databases/mysql/restore
#   sudo chmod 700 /data/databases/mysql/restore

# 配置参数
echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"localhost" -u"root" -p"$MYSQL_ROOT_PASSWORD" --silent; do
    sleep 2
done

BACKUP_FILE="/backups/mysql57_sysafari_20250723_qp.xb"
RESTORE_DIR="/data/databases/mysql/restore"
MYSQL_DATA_DIR="/var/lib/mysql"
MYSQL_USER="mysql"
MYSQL_GROUP="mysql"

if [ -f "$BACKUP_FILE" ]; then
    echo "Backup file found: $BACKUP_FILE"
    echo "Starting database restoration..."

    # 停止MySQL服务
    mysqladmin -u root -p"$MYSQL_ROOT_PASSWORD" shutdown || true
    sleep 5

    # 清空当前数据目录
    if [ -d "$MYSQL_DATA_DIR" ] && [ "$(ls -A $MYSQL_DATA_DIR)" ]; then
        echo "Clearing existing data..."
        rm -rf $MYSQL_DATA_DIR/*
    fi

    # 创建恢复目录
    echo "Creating restore directory: $RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"
    chown -R $MYSQL_USER:$MYSQL_GROUP "$RESTORE_DIR"
    chmod 700 "$RESTORE_DIR"
    echo "Restore directory created. Listing:"
    ls -ld "$RESTORE_DIR"

    # 步骤一：解包 .qp.xb 文件
    echo "Extracting backup file with xbstream..."
    cat "$BACKUP_FILE" | xbstream -x -v -C "$RESTORE_DIR"
    echo "After xbstream extraction, listing $RESTORE_DIR:"
    ls -lh "$RESTORE_DIR"

    # 步骤二：解压 .qp 文件（如有）
    if ls "$RESTORE_DIR"/*.qp &>/dev/null; then
        echo "Decompressing .qp files with innobackupex..."
        innobackupex --decompress --remove-original "$RESTORE_DIR"
        echo "After decompress, listing $RESTORE_DIR:"
        ls -lh "$RESTORE_DIR"
    else
        echo "No .qp files found, skipping decompress."
    fi

    # 检查 xtrabackup_checkpoints 是否存在
    if [ ! -f "$RESTORE_DIR/xtrabackup_checkpoints" ]; then
        echo "ERROR: xtrabackup_checkpoints not found in $RESTORE_DIR. Directory listing:"
        ls -lh "$RESTORE_DIR"
        exit 2
    fi

    # 应用日志并准备数据
    echo "Applying log to backup data..."
    innobackupex --apply-log "$RESTORE_DIR"

    # 拷贝数据到数据目录
    echo "Copying back data to MySQL data directory..."
    innobackupex --copy-back "$RESTORE_DIR"

    # 设置权限
    chown -R $MYSQL_USER:$MYSQL_GROUP $MYSQL_DATA_DIR

    echo "Database restoration completed successfully!"
else
    echo "Backup file not found: $BACKUP_FILE"
    echo "Skipping restoration. Please restore manually if needed."
fi
