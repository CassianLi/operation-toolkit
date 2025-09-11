#!/bin/bash
# CentOS 7 Python 3.8 保守编译脚本

set -e

echo "使用保守方法编译Python 3.8..."

# 1. 安装基础依赖
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel

# 2. 清理环境
cd /tmp
rm -rf Python-3.8.18

# 3. 下载Python 3.8.18
# 检查是否存在Python-3.8.18.tgz
if [ -f Python-3.8.18.tgz ]; then
    echo "Python-3.8.18.tgz 已存在"
else
    echo "Python-3.8.18.tgz 不存在"
    wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz
fi
tar -xzf Python-3.8.18.tgz
cd Python-3.8.18

# 4. 最小化配置（避免编译问题）
./configure \
    --prefix=/usr/local/python3.8 \
    --enable-shared \
    --with-ensurepip=install

# 5. 单线程编译（最稳定）
make

# 6. 安装
sudo make altinstall

# 7. 配置环境
echo '/usr/local/python3.8/lib' | sudo tee /etc/ld.so.conf.d/python3.8.conf
sudo ldconfig

# 8. 创建软链接
sudo ln -sf /usr/local/python3.8/bin/python3.8 /usr/bin/python3
sudo ln -sf /usr/local/python3.8/bin/pip3.8 /usr/bin/pip3

# 9. 验证
python3 --version
pip3 --version
