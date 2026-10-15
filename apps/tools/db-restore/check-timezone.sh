#!/bin/bash

echo "=== 时区设置验证脚本 ==="
echo

echo "1. 宿主机时区信息："
echo "当前时区：$(timedatectl show --property=Timezone --value)"
echo "本地时间：$(date)"
echo "UTC时间：$(date -u)"
echo

echo "2. 检查时区文件："
if [ -f "/etc/localtime" ]; then
    echo "✓ /etc/localtime 文件存在"
    echo "  链接目标：$(readlink /etc/localtime)"
else
    echo "✗ /etc/localtime 文件不存在"
fi

if [ -f "/etc/timezone" ]; then
    echo "✓ /etc/timezone 文件存在"
    echo "  内容：$(cat /etc/timezone)"
else
    echo "✗ /etc/timezone 文件不存在"
fi
echo

echo "3. 容器时区验证（如果容器正在运行）："
if command -v podman-compose &> /dev/null; then
    if podman-compose ps | grep -q mysql57; then
        echo "✓ MySQL容器正在运行"
        echo "容器内时区："
        podman-compose exec mysql57 date
        echo "容器内时区设置："
        podman-compose exec mysql57 cat /etc/timezone 2>/dev/null || echo "容器内无 /etc/timezone 文件"
        echo "容器内本地时间链接："
        podman-compose exec mysql57 readlink /etc/localtime 2>/dev/null || echo "容器内无 /etc/localtime 链接"
    else
        echo "✗ MySQL容器未运行，请先启动容器"
    fi
else
    echo "✗ podman-compose 未安装或不在PATH中"
fi
echo

echo "4. 网络时间同步状态："
if command -v timedatectl &> /dev/null; then
    echo "NTP同步状态：$(timedatectl show --property=NTP --value)"
    echo "NTP同步服务器：$(timedatectl show --property=NTPSynchronized --value)"
else
    echo "timedatectl 命令不可用"
fi
echo

echo "=== 验证完成 ==="
