#!/bin/bash
# CentOS 7 Python 3.8 改进编译脚本

set -e

echo "开始安装Python 3.8..."

# 1. 安装完整的开发依赖
echo "安装开发依赖..."
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    readline-devel \
    sqlite-devel \
    tk-devel \
    gdbm-devel \
    db4-devel \
    libpcap-devel \
    xz-devel \
    expat-devel \
    libuuid-devel \
    ncurses-devel

# 2. 检查内存和磁盘空间
echo "检查系统资源..."
free -h
df -h /tmp

# 3. 清理环境
cd /tmp
rm -rf Python-3.8.18*

# 4. 下载Python 3.8.18
echo "下载Python源码..."
if [ ! -f Python-3.8.18.tgz ]; then
    wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz
fi
tar -xzf Python-3.8.18.tgz
cd Python-3.8.18

# 5. 设置编译环境变量
export CFLAGS="-O2 -fPIC"
export LDFLAGS="-L/usr/lib64"
export CPPFLAGS="-I/usr/include"

# 6. 配置编译选项（更保守的配置）
echo "配置编译选项..."
./configure \
    --prefix=/usr/local/python3.8 \
    --enable-shared \
    --with-ensurepip=install \
    --disable-optimizations \
    --with-system-ffi \
    --enable-loadable-sqlite-extensions

# 7. 编译（使用单线程，更稳定）
echo "开始编译..."
make -j1

# 8. 安装
echo "安装Python..."
sudo make altinstall

# 9. 清理旧的软链接（避免冲突）
echo "清理旧的软链接..."
sudo rm -f /usr/bin/python3
sudo rm -f /usr/bin/pip3
sudo rm -f /usr/local/bin/python3
sudo rm -f /usr/local/bin/pip3

# 10. 配置环境
echo "配置环境..."
echo '/usr/local/python3.8/lib' | sudo tee /etc/ld.so.conf.d/python3.8.conf
sudo ldconfig

# 11. 创建软链接
echo "创建软链接..."
sudo ln -sf /usr/local/python3.8/bin/python3.8 /usr/bin/python3
sudo ln -sf /usr/local/python3.8/bin/pip3.8 /usr/bin/pip3

# 12. 更新环境变量
echo "更新环境变量..."
if ! echo $PATH | grep -q "/usr/local/python3.8/bin"; then
    echo 'export PATH="/usr/local/python3.8/bin:$PATH"' | sudo tee -a /etc/profile
    echo 'export PATH="/usr/local/python3.8/bin:$PATH"' >> ~/.bashrc
fi

# 13. 验证安装
echo "验证安装..."
echo "python3 路径: $(which python3)"
echo "python3 版本: $(python3 --version)"
echo "pip3 路径: $(which pip3)"
echo "pip3 版本: $(pip3 --version)"

# 14. 测试Python功能
echo "测试Python功能..."
python3 -c "import sys; print('Python路径:', sys.executable)"
python3 -c "import ssl; print('SSL模块正常')"
python3 -c "import json; print('JSON模块正常')"

echo "Python 3.8 安装完成！"
echo "如果遇到路径问题，请运行: source ~/.bashrc"
