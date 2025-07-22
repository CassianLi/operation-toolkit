# Linux登录用户权限管理脚本

这是一个专门用于管理Linux系统登录用户权限的脚本，不涉及应用程序运行权限。

## 功能特性

- ✅ 创建SSH登录用户
- ✅ 配置用户组权限（开发人员、运维人员、安全管理员、只读用户）
- ✅ 设置目录ACL权限
- ✅ 配置sudo权限
- ✅ 管理SSH密钥认证
- ✅ 自动依赖检查和安装

## 依赖要求

### 系统依赖
- `acl` - ACL权限管理工具
- `sudo` - sudo权限管理
- `shadow-utils` - 用户管理工具（useradd, groupadd等）
- `python3` - Python 3.6+
- `python3-pip` - Python包管理器

### Python依赖
- `colorama>=0.4.4` - 彩色终端输出

## 安装方法

### 方法一：自动安装（推荐）

1. 为安装脚本设置可执行权限：
```bash
chmod +x tools/install.sh
```

2. 运行安装脚本：
```bash
sudo ./tools/install.sh
```

### 方法二：手动安装

#### Ubuntu/Debian系统
```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install -y acl sudo passwd python3 python3-pip

# 安装Python依赖
pip3 install -r tools/requirements.txt
# 或者
pip3 install colorama>=0.4.4
```

#### CentOS/RHEL系统
```bash
# CentOS 8+ (使用dnf)
sudo dnf install -y acl sudo shadow-utils python3 python3-pip

# CentOS 7 (使用yum)
sudo yum install -y acl sudo shadow-utils python3 python3-pip

# 安装Python依赖
pip3 install -r tools/requirements.txt
```

#### openSUSE/SUSE系统
```bash
# 安装系统依赖
sudo zypper install -y acl sudo shadow python3 python3-pip

# 安装Python依赖
pip3 install -r tools/requirements.txt
```

#### Arch Linux系统
```bash
# 安装系统依赖
sudo pacman -S --noconfirm acl sudo shadow python python-pip

# 安装Python依赖
pip install -r tools/requirements.txt
```

## 使用方法

1. 确保以root权限运行：
```bash
sudo python3 tools/user_manager.py
```

2. 根据提示选择操作：
   - 创建登录用户并配置权限
   - 修改现有用户权限
   - 查看用户权限信息
   - 回收用户权限

## 用户组说明

### 1. developers（开发人员）
- **权限**：代码开发和调试权限
- **目录**：源码目录读写、系统日志只读
- **sudo**：服务管理、系统监控

### 2. operations（运维人员）
- **权限**：系统管理和维护权限
- **目录**：完整系统目录访问
- **sudo**：完整系统管理权限

### 3. security（安全管理员）
- **权限**：安全审计和配置权限
- **目录**：日志读写、配置只读
- **sudo**：安全工具和审计权限

### 4. readonly（只读用户）
- **权限**：仅查看权限，适用于审计监控
- **目录**：系统目录只读
- **sudo**：仅查看命令

## 注意事项

1. **权限说明**：此脚本仅管理登录用户权限，不涉及应用程序运行权限
2. **SSH配置**：用户创建后需要配置SSH公钥才能登录
3. **密码登录**：脚本创建的用户默认禁用密码登录，只能使用SSH密钥
4. **Root权限**：脚本需要root权限运行
5. **系统兼容性**：支持主流Linux发行版

## 文件说明

- `user_manager.py` - 主脚本文件
- `requirements.txt` - Python依赖列表
- `install.sh` - 自动安装脚本
- `README.md` - 使用说明文档

## 故障排除

### 依赖问题
脚本启动时会自动检查依赖，如果缺少依赖会提供安装命令。

### 权限问题
确保以root用户运行脚本：
```bash
sudo python3 tools/user_manager.py
```

### ACL支持问题
如果系统不支持ACL，需要安装acl工具包：
```bash
# Ubuntu/Debian
sudo apt-get install acl

# CentOS/RHEL
sudo yum install acl
```

## 版本信息

- 版本：2.0
- 更新：专注于登录用户权限管理，移除应用程序部署权限配置
- 兼容性：Python 3.6+，支持主流Linux发行版
