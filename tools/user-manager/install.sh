#!/bin/bash

# Linux登录用户权限管理脚本 - 依赖安装脚本
# 版本：2.0

set -e

echo "=============================================="
echo "  Linux登录用户权限管理脚本 - 依赖安装"
echo "=============================================="

# 检查是否以root用户运行
if [[ $EUID -ne 0 ]]; then
    echo "❌ 此脚本需要root权限运行"
    echo "请使用: sudo $0"
    exit 1
fi

echo "🔍 检测系统类型..."

# 检测操作系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
elif [ -f /etc/redhat-release ]; then
    OS="CentOS"
    VER=$(rpm -q --queryformat '%{VERSION}' centos-release)
else
    echo "❌ 无法检测操作系统类型"
    exit 1
fi

echo "📋 检测到系统: $OS $VER"

# 系统依赖包列表
declare -A PACKAGES
PACKAGES["acl"]="acl"
PACKAGES["sudo"]="sudo"
PACKAGES["shadow-utils"]="shadow-utils passwd"
PACKAGES["python3"]="python3"
PACKAGES["python3-pip"]="python3-pip"

echo "📦 安装系统依赖..."

# 根据系统类型安装依赖
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    echo "🐧 检测到Debian/Ubuntu系统"

    # 更新包列表
    echo "更新包列表..."
    apt-get update

    # 安装依赖
    echo "安装系统依赖..."
    apt-get install -y acl sudo passwd python3 python3-pip

elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
    echo "🔴 检测到RHEL/CentOS系统"

    # 检查是否有dnf命令（CentOS 8+）
    if command -v dnf &>/dev/null; then
        echo "使用DNF安装依赖..."
        dnf install -y acl sudo shadow-utils python3 python3-pip
    else
        echo "使用YUM安装依赖..."
        yum install -y acl sudo shadow-utils python3 python3-pip
    fi

elif [[ "$OS" == *"openSUSE"* ]] || [[ "$OS" == *"SUSE"* ]]; then
    echo "🦎 检测到openSUSE/SUSE系统"
    zypper install -y acl sudo shadow python3 python3-pip

elif [[ "$OS" == *"Arch"* ]]; then
    echo "🏛️ 检测到Arch Linux系统"
    pacman -S --noconfirm acl sudo shadow python python-pip

else
    echo "⚠️  未识别的系统类型: $OS"
    echo "请手动安装以下软件包："
    echo "- acl"
    echo "- sudo"
    echo "- shadow-utils/passwd"
    echo "- python3"
    echo "- python3-pip"
    exit 1
fi

echo "✅ 系统依赖安装完成"

# 安装Python依赖
echo "🐍 安装Python依赖..."

# 检查是否存在requirements.txt
if [ -f "$(dirname "$0")/requirements.txt" ]; then
    echo "使用requirements.txt安装Python依赖..."
    pip3 install -r "$(dirname "$0")/requirements.txt"
else
    echo "直接安装Python依赖..."
    pip3 install colorama >=0.4.4
fi

echo "✅ Python依赖安装完成"

# 验证安装
echo "🔍 验证安装..."

# 检查关键命令
commands=("setfacl" "visudo" "useradd" "groupadd" "python3")
for cmd in "${commands[@]}"; do
    if command -v "$cmd" &>/dev/null; then
        echo "✅ $cmd 已安装"
    else
        echo "❌ $cmd 未找到"
        exit 1
    fi
done

# 检查Python模块
echo "检查Python模块..."
python3 -c "import colorama; print('✅ colorama 已安装')" 2>/dev/null || {
    echo "❌ colorama 未安装"
    exit 1
}

echo ""
echo "🎉 所有依赖安装完成！"
echo ""
echo "现在可以运行用户管理脚本："
echo "sudo python3 $(dirname "$0")/user_manager.py"
echo ""
