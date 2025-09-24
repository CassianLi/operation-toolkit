#!/bin/bash
# Python版本清理和配置脚本

set -e

echo "开始清理Python版本冲突..."

# 1. 检查当前Python安装情况
echo "=== 当前Python安装情况 ==="
echo "which python3: $(which python3 2>/dev/null || echo 'not found')"
echo "which python3.7: $(which python3.7 2>/dev/null || echo 'not found')"
echo "which python3.8: $(which python3.8 2>/dev/null || echo 'not found')"

echo -e "\n=== PATH中的Python路径 ==="
echo $PATH | tr ':' '\n' | grep -E "(python|bin)" | sort -u

echo -e "\n=== 系统中的Python可执行文件 ==="
find /usr/bin /usr/local/bin -name "python*" -type f 2>/dev/null | sort

# 2. 备份当前配置
echo -e "\n=== 备份当前配置 ==="
sudo cp /etc/profile /etc/profile.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
sudo cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# 3. 清理旧的软链接
echo -e "\n=== 清理旧的软链接 ==="
sudo rm -f /usr/bin/python3
sudo rm -f /usr/bin/pip3
sudo rm -f /usr/local/bin/python3
sudo rm -f /usr/local/bin/pip3

# 4. 检查Python 3.8是否正确安装
echo -e "\n=== 检查Python 3.8安装 ==="
if [ -f "/usr/local/python3.8/bin/python3.8" ]; then
    echo "Python 3.8 已安装在 /usr/local/python3.8/"
    /usr/local/python3.8/bin/python3.8 --version
else
    echo "错误: Python 3.8 未正确安装"
    exit 1
fi

# 5. 创建正确的软链接
echo -e "\n=== 创建正确的软链接 ==="
sudo ln -sf /usr/local/python3.8/bin/python3.8 /usr/bin/python3
sudo ln -sf /usr/local/python3.8/bin/pip3.8 /usr/bin/pip3

# 6. 更新库路径配置
echo -e "\n=== 更新库路径配置 ==="
echo '/usr/local/python3.8/lib' | sudo tee /etc/ld.so.conf.d/python3.8.conf
sudo ldconfig

# 7. 清理可能的Python 3.7残留
echo -e "\n=== 清理Python 3.7残留 ==="
# 查找并移除可能的Python 3.7软链接
sudo find /usr/bin /usr/local/bin -name "python3.7*" -type l -delete 2>/dev/null || true

# 8. 更新环境变量
echo -e "\n=== 更新环境变量 ==="
# 确保/usr/local/python3.8/bin在PATH中
if ! echo $PATH | grep -q "/usr/local/python3.8/bin"; then
    echo 'export PATH="/usr/local/python3.8/bin:$PATH"' >> ~/.bashrc
    echo "已添加Python 3.8路径到 ~/.bashrc"
fi

# 9. 验证安装
echo -e "\n=== 验证安装 ==="
echo "重新加载环境变量..."
source ~/.bashrc 2>/dev/null || true

echo "python3 路径: $(which python3)"
echo "python3 版本: $(python3 --version)"
echo "pip3 路径: $(which pip3)"
echo "pip3 版本: $(pip3 --version)"

# 10. 测试Python功能
echo -e "\n=== 测试Python功能 ==="
python3 -c "import sys; print('Python路径:', sys.executable)"
python3 -c "import ssl; print('SSL模块正常')"
python3 -c "import json; print('JSON模块正常')"

echo -e "\n=== 清理完成 ==="
echo "如果仍有问题，请执行以下命令重新加载环境："
echo "source ~/.bashrc"
echo "或者重新登录终端"
